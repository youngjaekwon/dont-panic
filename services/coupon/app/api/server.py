import grpc
from coupon.v1 import coupon_pb2_grpc
from dishka import AsyncContainer
from dishka.integrations.grpcio import DishkaAioInterceptor

from app.api.servicer import CouponServicer


async def start_grpc_server(container: AsyncContainer, port: int) -> grpc.aio.Server:
    server = grpc.aio.server(interceptors=[DishkaAioInterceptor(container)])
    coupon_pb2_grpc.add_CouponServiceServicer_to_server(CouponServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    return server
