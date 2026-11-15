import datetime

from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateCampaignRequest(_message.Message):
    __slots__ = ("name", "total_quantity", "starts_at")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TOTAL_QUANTITY_FIELD_NUMBER: _ClassVar[int]
    STARTS_AT_FIELD_NUMBER: _ClassVar[int]
    name: str
    total_quantity: int
    starts_at: _timestamp_pb2.Timestamp
    def __init__(self, name: _Optional[str] = ..., total_quantity: _Optional[int] = ..., starts_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetCampaignRequest(_message.Message):
    __slots__ = ("campaign_id",)
    CAMPAIGN_ID_FIELD_NUMBER: _ClassVar[int]
    campaign_id: int
    def __init__(self, campaign_id: _Optional[int] = ...) -> None: ...

class ListCouponsRequest(_message.Message):
    __slots__ = ("campaign_id", "page_size", "page_token")
    CAMPAIGN_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    campaign_id: int
    page_size: int
    page_token: str
    def __init__(self, campaign_id: _Optional[int] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListCouponsResponse(_message.Message):
    __slots__ = ("coupons", "next_page_token")
    COUPONS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    coupons: _containers.RepeatedCompositeFieldContainer[Coupon]
    next_page_token: str
    def __init__(self, coupons: _Optional[_Iterable[_Union[Coupon, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class IssueCouponRequest(_message.Message):
    __slots__ = ("campaign_id",)
    CAMPAIGN_ID_FIELD_NUMBER: _ClassVar[int]
    campaign_id: int
    def __init__(self, campaign_id: _Optional[int] = ...) -> None: ...

class IssueCouponResponse(_message.Message):
    __slots__ = ("code",)
    CODE_FIELD_NUMBER: _ClassVar[int]
    code: str
    def __init__(self, code: _Optional[str] = ...) -> None: ...

class Coupon(_message.Message):
    __slots__ = ("code", "issued_at")
    CODE_FIELD_NUMBER: _ClassVar[int]
    ISSUED_AT_FIELD_NUMBER: _ClassVar[int]
    code: str
    issued_at: _timestamp_pb2.Timestamp
    def __init__(self, code: _Optional[str] = ..., issued_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Campaign(_message.Message):
    __slots__ = ("id", "name", "total_quantity", "issued_count", "starts_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TOTAL_QUANTITY_FIELD_NUMBER: _ClassVar[int]
    ISSUED_COUNT_FIELD_NUMBER: _ClassVar[int]
    STARTS_AT_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    total_quantity: int
    issued_count: int
    starts_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., total_quantity: _Optional[int] = ..., issued_count: _Optional[int] = ..., starts_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
