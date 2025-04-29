import argparse
import os
import pyotp
from datetime import datetime, timedelta, timezone
import re

def parse_args():
    parser = argparse.ArgumentParser(description='Generate TOTP tokens for specific time(s).')
    parser.add_argument('--time', required=True, help='Start time in HH:MM format (24h)')
    parser.add_argument('--count', type=int, default=3, help='Number of 30-second tokens to generate (default: 3)')
    parser.add_argument('--date', help='Date in YYYY-MM-DD format')
    parser.add_argument('--days', type=int, default=3, help='Generate tokens for the next X days if --date is not set (default: 3)')
    parser.add_argument('--secret', help='Base32-encoded TOTP secret key (or use TOTP_SECRET env var)')
    parser.add_argument('--tz', default='UTC-3', help='Timezone offset, e.g. UTC, UTC+2, UTC-5 (default: UTC-3)')
    return parser.parse_args()

def parse_timezone(tz_str):
    match = re.fullmatch(r'UTC([+-]?)(\d{1,2})?', tz_str.strip().upper())
    if not match:
        raise ValueError(f'Invalid timezone format: {tz_str}. Use formats like UTC, UTC+3, UTC-2')

    sign = match.group(1) or '+'
    offset_hours = int(match.group(2) or 0)
    delta = timedelta(hours=offset_hours)
    return timezone(delta if sign == '+' else -delta)

def get_secret(cli_secret):
    secret = cli_secret or os.getenv("TOTP_SECRET")
    if not secret:
        raise ValueError("No secret provided. Use --secret or set the TOTP_SECRET environment variable.")
    return secret

def get_timestamps(start_time: str, tz: timezone, date_str: str = None, days: int = 3):
    time_parts = datetime.strptime(start_time, '%H:%M').time()

    if date_str:
        base_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        dates = [base_date]
    else:
        today = datetime.now(tz=tz).date()
        dates = [today + timedelta(days=i) for i in range(days)]

    timestamps = []
    for d in dates:
        dt = datetime.combine(d, time_parts)
        dt = dt.replace(tzinfo=tz)
        timestamps.append(int(dt.timestamp()))
    return timestamps

def generate_totps(secret, base_timestamps, count):
    totp = pyotp.TOTP(secret)
    for ts in base_timestamps:
        print(f'\nTokens starting at {datetime.fromtimestamp(ts)}:')
        for i in range(count):
            target_ts = ts + i * 30
            otp = totp.at(target_ts)
            readable_time = datetime.fromtimestamp(target_ts).strftime('%Y-%m-%d %H:%M:%S')
            print(f'  {readable_time} -> {otp}')

def main():
    args = parse_args()
    try:
        tz = parse_timezone(args.tz)
        secret = get_secret(args.secret)
        timestamps = get_timestamps(args.time, tz, args.date, args.days)
        generate_totps(secret, timestamps, args.count)
    except ValueError as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    main()

