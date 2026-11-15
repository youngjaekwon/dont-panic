from datetime import UTC, datetime

import grpc
from coupon.v1 import coupon_pb2 as pb
from coupon.v1 import coupon_pb2_grpc as pb_grpc
from dishka.integrations.grpcio import FromDishka, inject
from google.protobuf.timestamp_pb2 import Timestamp

from app.models import Campaign
from app.services.coupon_service import CouponService
from app.services.exceptions import CouponError, NotFound, NotStarted, SoldOut

ERRORS = {
    NotFound: (grpc.StatusCode.NOT_FOUND, "campaign not found"),
    NotStarted: (grpc.StatusCode.FAILED_PRECONDITION, "campaign not started"),
    SoldOut: (grpc.StatusCode.RESOURCE_EXHAUSTED, "sold out"),
}

DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000
MAX_SEQ = 2**31 - 1


def _ts(dt: datetime) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


def _campaign(c: Campaign, issued_count: int) -> pb.Campaign:
    return pb.Campaign(
        id=c.id,
        name=c.name,
        total_quantity=c.total_quantity,
        issued_count=issued_count,
        starts_at=_ts(c.starts_at),
    )


def _page_args(request) -> tuple[int, int]:
    if request.page_size < 0:
        raise ValueError("page_size must not be negative")
    try:
        after_seq = int(request.page_token or 0)
    except ValueError:
        raise ValueError("invalid page_token") from None
    if not 0 <= after_seq <= MAX_SEQ:
        raise ValueError("invalid page_token")
    return after_seq, min(request.page_size or DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE)


class CouponServicer(pb_grpc.CouponServiceServicer):
    @inject
    async def CreateCampaign(self, request, context, service: FromDishka[CouponService]):
        if not request.HasField("starts_at"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "starts_at required")
        try:
            starts_at = request.starts_at.ToDatetime(tzinfo=UTC)
            return _campaign(await service.create_campaign(request.name, request.total_quantity, starts_at), 0)
        except ValueError as e:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))

    @inject
    async def GetCampaign(self, request, context, service: FromDishka[CouponService]):
        try:
            return _campaign(*await service.get_campaign(request.campaign_id))
        except CouponError as e:
            await context.abort(*ERRORS[type(e)])

    @inject
    async def ListCoupons(self, request, context, service: FromDishka[CouponService]):
        try:
            after_seq, size = _page_args(request)
            page = await service.list_coupons(request.campaign_id, after_seq, size)
            return pb.ListCouponsResponse(
                coupons=[pb.Coupon(code=x.code, issued_at=_ts(x.issued_at)) for x in page],
                next_page_token=str(page[-1].seq) if len(page) == size else "",
            )
        except ValueError as e:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except CouponError as e:
            await context.abort(*ERRORS[type(e)])

    @inject
    async def IssueCoupon(self, request, context, service: FromDishka[CouponService]):
        try:
            return pb.IssueCouponResponse(code=await service.issue(request.campaign_id))
        except CouponError as e:
            await context.abort(*ERRORS[type(e)])
