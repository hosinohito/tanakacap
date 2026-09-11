// Enumerate the camera names and native modes directly through Windows Media Foundation.
#include <windows.h>
#include <mfapi.h>
#include <mferror.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <wrl/client.h>
#include <iostream>
#include <stdexcept>
using Microsoft::WRL::ComPtr;

void check(HRESULT value, const char* operation) {
    if (FAILED(value)) {
        std::cerr << operation << " failed: 0x" << std::hex << value << std::dec << "\n";
        throw std::runtime_error(operation);
    }
}
int main() {
    try {
        check(CoInitializeEx(nullptr, COINIT_MULTITHREADED), "CoInitializeEx");
        check(MFStartup(MF_VERSION), "MFStartup");
        {
            ComPtr<IMFAttributes> attributes;
            check(MFCreateAttributes(&attributes, 1), "MFCreateAttributes");
            check(attributes->SetGUID(MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE,
                                     MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE_VIDCAP_GUID), "SetGUID");
            IMFActivate** devices = nullptr;
            UINT32 count = 0;
            check(MFEnumDeviceSources(attributes.Get(), &devices, &count), "MFEnumDeviceSources");
            for (UINT32 i = 0; i < count; ++i) {
                WCHAR* name = nullptr;
                UINT32 length = 0;
                devices[i]->GetAllocatedString(MF_DEVSOURCE_ATTRIBUTE_FRIENDLY_NAME, &name, &length);
                std::wcout << L"DEVICE " << i << L": " << (name ? name : L"unknown") << L"\n";
                CoTaskMemFree(name);
                ComPtr<IMFMediaSource> source;
                HRESULT activated = devices[i]->ActivateObject(IID_PPV_ARGS(&source));
                if (SUCCEEDED(activated)) {
                    ComPtr<IMFSourceReader> reader;
                    HRESULT created = MFCreateSourceReaderFromMediaSource(source.Get(), nullptr, &reader);
                    if (SUCCEEDED(created)) {
                        for (DWORD mode = 0; ; ++mode) {
                            ComPtr<IMFMediaType> type;
                            HRESULT found = reader->GetNativeMediaType(static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM), mode, &type);
                            if (found == MF_E_NO_MORE_TYPES) break;
                            if (FAILED(found)) break;
                            UINT32 width = 0, height = 0, numerator = 0, denominator = 0;
                            GUID subtype = {};
                            MFGetAttributeSize(type.Get(), MF_MT_FRAME_SIZE, &width, &height);
                            MFGetAttributeRatio(type.Get(), MF_MT_FRAME_RATE, &numerator, &denominator);
                            type->GetGUID(MF_MT_SUBTYPE, &subtype);
                            wchar_t format[5] = {};
                            for (int j = 0; j < 4; ++j) {
                                unsigned char c = (subtype.Data1 >> (j*8)) & 255;
                                format[j] = (c >= 32 && c <= 126) ? c : L'?';
                            }
                            std::wcout << L"  " << width << L"x" << height << L" "
                                       << numerator << L"/" << denominator << L" fps " << format << L"\n";
                        }
                    }
                    reader.Reset();
                    source->Shutdown();
                } else {
                    std::wcout << L"  activation failed: " << std::hex << activated << std::dec << L"\n";
                }
                devices[i]->ShutdownObject();
                devices[i]->Release();
            }
            CoTaskMemFree(devices);
        }
        MFShutdown();
        CoUninitialize();
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << "\n";
        return 1;
    }
}
