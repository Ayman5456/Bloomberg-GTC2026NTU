"""Check Desktop API connectivity without requesting any market data."""
import sys


def main():
    try:
        import blpapi
    except ImportError as exc:
        print(f"BLPAPI import failed: {exc}", file=sys.stderr)
        return 1

    print(f"Python: {sys.executable}")
    print(f"BLPAPI: {blpapi.version()}")
    options = blpapi.SessionOptions()
    options.setServerHost("127.0.0.1")
    options.setServerPort(8194)
    options.setClientMode(blpapi.SessionOptions.DAPI)
    options.setConnectTimeout(5000)
    options.setNumStartAttempts(1)
    options.setServiceCheckTimeout(5000)
    options.setServiceDownloadTimeout(10000)
    session = blpapi.Session(options)
    try:
        if not session.start():
            print("FAIL: Bloomberg Desktop API session could not start.")
            return 2
        print("PASS: Bloomberg session started.")
        if not session.openService("//blp/refdata"):
            print("FAIL: Reference-data service could not open.")
            return 3
        print("PASS: Reference-data service opened. No market data requested.")
        print("Security and field entitlements remain untested.")
        return 0
    finally:
        session.stop()


if __name__ == "__main__":
    sys.exit(main())
