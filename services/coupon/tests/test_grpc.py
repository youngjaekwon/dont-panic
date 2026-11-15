from datetime import UTC, datetime, timedelta

import grpc
import pytest
from coupon.v1 import coupon_pb2 as pb
from coupon.v1 import coupon_pb2_grpc as pb_grpc

from app.api.server import start_grpc_server

TEST_PORT = 50052


@pytest.fixture
async def stub(container):
    server = await start_grpc_server(container, TEST_PORT)
    async with grpc.aio.insecure_channel(f"localhost:{TEST_PORT}") as channel:
        yield pb_grpc.CouponServiceStub(channel)
    await server.stop(grace=None)


async def status_of(call) -> grpc.StatusCode:
    with pytest.raises(grpc.aio.AioRpcError) as e:
        await call
    return e.value.code()


async def test_issue_until_sold_out(stub):
    started = datetime.now(UTC) - timedelta(seconds=1)
    c = await stub.CreateCampaign(pb.CreateCampaignRequest(name="a", total_quantity=3, starts_at=started))

    codes = [(await stub.IssueCoupon(pb.IssueCouponRequest(campaign_id=c.id))).code for _ in range(3)]
    assert (
        await status_of(stub.IssueCoupon(pb.IssueCouponRequest(campaign_id=c.id))) == grpc.StatusCode.RESOURCE_EXHAUSTED
    )

    got = await stub.GetCampaign(pb.GetCampaignRequest(campaign_id=c.id))
    assert got.issued_count == 3

    listed, token = [], ""
    for _ in range(3):
        page = await stub.ListCoupons(pb.ListCouponsRequest(campaign_id=c.id, page_size=2, page_token=token))
        listed += [x.code for x in page.coupons]
        token = page.next_page_token
        if not token:
            break
    assert sorted(listed) == sorted(codes)


async def test_error_status_codes(stub):
    future = datetime.now(UTC) + timedelta(hours=1)
    c = await stub.CreateCampaign(pb.CreateCampaignRequest(name="b", total_quantity=5, starts_at=future))

    assert (
        await status_of(stub.IssueCoupon(pb.IssueCouponRequest(campaign_id=c.id)))
        == grpc.StatusCode.FAILED_PRECONDITION
    )
    assert await status_of(stub.IssueCoupon(pb.IssueCouponRequest(campaign_id=2**62))) == grpc.StatusCode.NOT_FOUND
    assert await status_of(stub.GetCampaign(pb.GetCampaignRequest(campaign_id=2**62))) == grpc.StatusCode.NOT_FOUND
    assert await status_of(stub.ListCoupons(pb.ListCouponsRequest(campaign_id=2**62))) == grpc.StatusCode.NOT_FOUND
    for token in ["abc", "-1", "²", str(2**31)]:
        assert (
            await status_of(stub.ListCoupons(pb.ListCouponsRequest(campaign_id=c.id, page_token=token)))
            == grpc.StatusCode.INVALID_ARGUMENT
        )
    assert (
        await status_of(stub.ListCoupons(pb.ListCouponsRequest(campaign_id=c.id, page_size=-1)))
        == grpc.StatusCode.INVALID_ARGUMENT
    )
    assert (
        await status_of(stub.CreateCampaign(pb.CreateCampaignRequest(name="x", total_quantity=1)))
        == grpc.StatusCode.INVALID_ARGUMENT
    )
    assert (
        await status_of(stub.CreateCampaign(pb.CreateCampaignRequest(name="x", total_quantity=0, starts_at=future)))
        == grpc.StatusCode.INVALID_ARGUMENT
    )
