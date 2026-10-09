// Connection-only test: no requests or subscriptions are sent.
#include <blpapi_session.h>
#include <blpapi_sessionoptions.h>
#include <iostream>

int main() {
    using namespace BloombergLP;
    blpapi::SessionOptions options;
    options.setServerHost("127.0.0.1");
    options.setServerPort(8194);
    options.setClientMode(blpapi::SessionOptions::DAPI);
    options.setConnectTimeout(5000);
    options.setNumStartAttempts(1);
    options.setServiceCheckTimeout(5000);
    options.setServiceDownloadTimeout(10000);
    blpapi::Session session(options);
    if (!session.start()) {
        std::cerr << "FAIL: Bloomberg session could not start.\n";
        return 2;
    }
    bool opened = session.openService("//blp/refdata");
    session.stop();
    if (!opened) {
        std::cerr << "FAIL: Reference-data service could not open.\n";
        return 3;
    }
    std::cout << "PASS: Session and reference-data service opened.\n"
              << "No market data requested; entitlements remain untested.\n";
    return 0;
}
