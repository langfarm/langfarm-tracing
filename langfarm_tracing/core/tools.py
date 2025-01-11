import uuid
from datetime import datetime, timezone


def format_datetime(dt: datetime) -> str:
    return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S.%f')


def utc_time_to_ltz(utc_str: str) -> datetime:
    utc = datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    ltz = utc.replace(tzinfo=timezone.utc).astimezone()
    return ltz


def rewrite_uuid(origin_uuid: str, time_str: str) -> uuid.UUID:
    ltz = utc_time_to_ltz(time_str)
    # 100 纳秒 也是 0.1 微秒
    nanoseconds_100 = int(ltz.timestamp() * 1000000) * 10
    # UUID epoch
    uuid_epoch = nanoseconds_100 + 0x01b21dd213814000
    time_low = uuid_epoch & 0xffffffff
    time_mid = (uuid_epoch >> 32) & 0xffff
    time_hi_version = (uuid_epoch >> 48) & 0x0fff

    # UUID
    old_v4 = uuid.UUID(origin_uuid)
    clock_seq_hi_variant = old_v4.clock_seq_hi_variant
    clock_seq_low = old_v4.clock_seq_low
    node = old_v4.node
    new_v4 = uuid.UUID(
        fields=(time_low, time_mid, time_hi_version, clock_seq_hi_variant, clock_seq_low, node)
        , version=4
    )
    return new_v4
