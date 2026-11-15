class CouponError(Exception):
    pass


class NotFound(CouponError):
    pass


class NotStarted(CouponError):
    pass


class SoldOut(CouponError):
    pass
