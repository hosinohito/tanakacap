// Development-only numeric capture probe. No renderer, image files, or audio stream.
#include <windows.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <mferror.h>
#include <dshow.h>
#include <ks.h>
#include <ksmedia.h>
#include <ksproxy.h>
#include <wrl/client.h>
#include <chrono>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using Microsoft::WRL::ComPtr;
void check(HRESULT hr, const char* operation) {
    if (FAILED(hr)) { std::cout << "{\"error\":\"" << operation << "\",\"hr\":" << hr << "}\n"; throw std::runtime_error(operation); }
}
struct Device {
    ComPtr<IMFMediaSource> source;
    int index = -1;
    Device() {
        ComPtr<IMFAttributes> attrs;
        check(MFCreateAttributes(&attrs, 1), "attributes");
        check(attrs->SetGUID(MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE, MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE_VIDCAP_GUID), "video-only");
        IMFActivate** devices = nullptr; UINT32 count = 0;
        check(MFEnumDeviceSources(attrs.Get(), &devices, &count), "enumerate");
        int matches = 0;
        for (UINT32 i=0; i<count; ++i) {
            WCHAR* name=nullptr; UINT32 length=0;
            devices[i]->GetAllocatedString(MF_DEVSOURCE_ATTRIBUTE_FRIENDLY_NAME, &name, &length);
            if (name && std::wstring(name).find(L"CMS-V43BK")!=std::wstring::npos) { index=static_cast<int>(i); ++matches; }
            CoTaskMemFree(name);
        }
        HRESULT hr=E_FAIL;
        if (matches==1) hr=devices[index]->ActivateObject(IID_PPV_ARGS(&source));
        for (UINT32 i=0; i<count; ++i) devices[i]->Release();
        CoTaskMemFree(devices);
        check(hr, "unique CMS-V43BK activation");
        std::cout << "{\"mf_index\":" << index << "}\n";
    }
    ~Device() { if(source) source->Shutdown(); }
};
struct Controls {
    ComPtr<IKsControl> ks;
    ComPtr<IAMCameraControl> camera;
    long power=0, powerFlags=0, exposure=0, exposureFlags=0;
    long minimum=0, maximum=0, step=0, defaultValue=0, caps=0;
    bool hasPower=false, hasExposure=false, changedPower=false, changedExposure=false;
    HRESULT powerProperty(bool write, long& value, long& flags) {
        if (!ks) return E_NOINTERFACE;
        KSPROPERTY_VIDEOPROCAMP_S p={};
        p.Property.Set=PROPSETID_VIDCAP_VIDEOPROCAMP;
        p.Property.Id=KSPROPERTY_VIDEOPROCAMP_POWERLINE_FREQUENCY;
        p.Property.Flags=write?KSPROPERTY_TYPE_SET:KSPROPERTY_TYPE_GET;
        p.Value=value; p.Flags=flags; ULONG returned=0;
        HRESULT hr=ks->KsProperty(&p.Property,sizeof(p),&p,sizeof(p),&returned);
        if(SUCCEEDED(hr)) { value=p.Value; flags=p.Flags; }
        return hr;
    }
    Controls(IMFMediaSource* source) {
        source->QueryInterface(IID_PPV_ARGS(&ks));
        source->QueryInterface(IID_PPV_ARGS(&camera));
        hasPower=SUCCEEDED(powerProperty(false,power,powerFlags));
        hasExposure=camera && SUCCEEDED(camera->Get(CameraControl_Exposure,&exposure,&exposureFlags)) &&
            SUCCEEDED(camera->GetRange(CameraControl_Exposure,&minimum,&maximum,&step,&defaultValue,&caps));
        std::cout << "{\"controls\":{\"power_available\":" << hasPower << ",\"power\":" << power
            << ",\"power_flags\":" << powerFlags << ",\"exposure_available\":" << hasExposure
            << ",\"exposure\":" << exposure << ",\"exposure_flags\":" << exposureFlags
            << ",\"minimum\":" << minimum << ",\"maximum\":" << maximum << ",\"step\":" << step << ",\"caps\":" << caps << "}}\n";
    }
    void setPower(long value, long flags) {
        if(!hasPower) throw std::runtime_error("powerline unsupported; skipped");
        const long requested=value;
        changedPower=true; // Restore even when a driver partly applies a failed request.
        check(powerProperty(true,value,flags),"set powerline");
        long actual=0, actualFlags=0;
        check(powerProperty(false,actual,actualFlags),"read powerline");
        std::cout << "{\"applied_power\":" << actual << ",\"applied_power_flags\":" << actualFlags << "}\n";
        if(actual!=requested) throw std::runtime_error("powerline request not applied");
    }
    void setExposure(long value, long flags) {
        if(!hasExposure) throw std::runtime_error("exposure unsupported; skipped");
        if(value<minimum || value>maximum || (step>0 && (value-minimum)%step)) throw std::runtime_error("exposure outside supported steps");
        if(!(caps & flags)) throw std::runtime_error("exposure mode unsupported");
        changedExposure=true;
        check(camera->Set(CameraControl_Exposure,value,flags),"set exposure");
        long actual=0, actualFlags=0;
        check(camera->Get(CameraControl_Exposure,&actual,&actualFlags),"read exposure");
        std::cout << "{\"applied_exposure\":" << actual << ",\"applied_exposure_flags\":" << actualFlags << "}\n";
        if(actualFlags!=flags || (flags==CameraControl_Flags_Manual && actual!=value)) throw std::runtime_error("exposure request not applied");
    }
    bool restore() {
        bool ok=true;
        if(changedExposure) {
            if(!camera) { std::cout << "{\"restore_exposure\":0}\n"; return false; }
            HRESULT hr=camera->Set(CameraControl_Exposure,exposure,exposureFlags);
            long v=0,f=0; bool matched=SUCCEEDED(hr) && SUCCEEDED(camera->Get(CameraControl_Exposure,&v,&f)) && f==exposureFlags && ((f&CameraControl_Flags_Auto)||v==exposure);
            std::cout << "{\"restore_exposure\":" << matched << "}\n"; ok &= matched; if(matched) changedExposure=false;
        }
        if(changedPower) {
            long v=power,f=powerFlags; HRESULT hr=powerProperty(true,v,f);
            bool matched=SUCCEEDED(hr) && SUCCEEDED(powerProperty(false,v,f)) && v==power && f==powerFlags;
            std::cout << "{\"restore_power\":" << matched << "}\n"; ok &= matched; if(matched) changedPower=false;
        }
        return ok;
    }
    ~Controls() { restore(); }
};
int main(int argc,char** argv) {
    std::cout << std::unitbuf;
    if(argc<2) { std::cerr << "Use inspect, capture, power VALUE, exposure VALUE FLAGS, restore POWER FLAGS EXPOSURE FLAGS\n"; return 2; }
    if(std::string(argv[1])=="--help") return 0;
    HRESULT init=CoInitializeEx(nullptr,COINIT_MULTITHREADED);
    if(FAILED(init)) return 1;
    HRESULT startup=MFStartup(MF_VERSION);
    if(FAILED(startup)) { CoUninitialize(); return 1; }
    int result=0;
    try {
        Device device;
        Controls controls(device.source.Get());
        std::string action=argv[1];
        if(action=="restore") {
            if(argc!=6) throw std::runtime_error("restore arguments");
            if(std::string(argv[2])!="skip") {
                controls.power=std::stol(argv[2]); controls.powerFlags=std::stol(argv[3]); controls.changedPower=true;
            }
            if(std::string(argv[4])!="skip") {
                controls.exposure=std::stol(argv[4]); controls.exposureFlags=std::stol(argv[5]); controls.changedExposure=true;
                if(!controls.camera) throw std::runtime_error("restore exposure interface unavailable");
            }
            if(!controls.restore()) result=3;
        } else {
            ComPtr<IMFSourceReader> reader;
            check(MFCreateSourceReaderFromMediaSource(device.source.Get(),nullptr,&reader),"source reader");
            constexpr DWORD stream=static_cast<DWORD>(MF_SOURCE_READER_FIRST_VIDEO_STREAM);
            ComPtr<IMFMediaType> chosen;
            for(DWORD i=0;;++i) {
                ComPtr<IMFMediaType> type;
                HRESULT hr=reader->GetNativeMediaType(stream,i,&type);
                if(hr==MF_E_NO_MORE_TYPES) break;
                check(hr,"native media type");
                UINT32 w=0,h=0,n=0,d=0; GUID subtype={};
                MFGetAttributeSize(type.Get(),MF_MT_FRAME_SIZE,&w,&h);
                MFGetAttributeRatio(type.Get(),MF_MT_FRAME_RATE,&n,&d);
                type->GetGUID(MF_MT_SUBTYPE,&subtype);
                std::cout << "{\"mode\":{\"width\":" << w << ",\"height\":" << h << ",\"numerator\":" << n << ",\"denominator\":" << d << ",\"fourcc\":" << subtype.Data1 << "}}\n";
                if(w==1280 && h==720 && d && n/double(d)>29.9 && n/double(d)<30.1 && subtype==MFVideoFormat_MJPG) chosen=type;
            }
            if(action!="inspect") {
                if(!chosen) throw std::runtime_error("native 720p MJPEG 30fps mode unavailable; no substitution");
                check(reader->SetCurrentMediaType(stream,nullptr,chosen.Get()),"select native 720p MJPEG 30fps together");
                ComPtr<IMFMediaType> current;
                check(reader->GetCurrentMediaType(stream,&current),"read negotiated media type");
                UINT32 width=0,height=0,num=0,den=0; GUID format={};
                check(MFGetAttributeSize(current.Get(),MF_MT_FRAME_SIZE,&width,&height),"negotiated size");
                check(MFGetAttributeRatio(current.Get(),MF_MT_FRAME_RATE,&num,&den),"negotiated rate");
                check(current->GetGUID(MF_MT_SUBTYPE,&format),"negotiated format");
                std::cout << "{\"selected\":{\"width\":" << width << ",\"height\":" << height << ",\"numerator\":" << num
                    << ",\"denominator\":" << den << ",\"fourcc\":" << format.Data1 << "}}\n";
                if(width!=1280 || height!=720 || !den || num/double(den)<29.9 || num/double(den)>30.1 || format!=MFVideoFormat_MJPG)
                    throw std::runtime_error("negotiated native mode mismatch");
                if(action=="power" && argc==3) controls.setPower(std::stol(argv[2]),KSPROPERTY_VIDEOPROCAMP_FLAGS_MANUAL);
                else if(action=="exposure" && argc==4) controls.setExposure(std::stol(argv[2]),std::stol(argv[3]));
                else if(action!="capture") throw std::runtime_error("unknown capture action");
                auto begin=std::chrono::steady_clock::now(), first=begin, last=begin;
                LONGLONG firstStamp=0,lastStamp=0;
                int count=0;
                // Discard 30 settling samples. No sample bytes are accessed or saved.
                while(count<150) {
                    DWORD flags=0; LONGLONG stamp=0; ComPtr<IMFSample> sample;
                    check(reader->ReadSample(stream,0,nullptr,&flags,&stamp,&sample),"read sample");
                    if(flags & (MF_SOURCE_READERF_ERROR|MF_SOURCE_READERF_ENDOFSTREAM)) throw std::runtime_error("capture stopped");
                    if(flags & (MF_SOURCE_READERF_CURRENTMEDIATYPECHANGED|MF_SOURCE_READERF_NATIVEMEDIATYPECHANGED)) throw std::runtime_error("capture format changed; comparison invalid");
                    auto now=std::chrono::steady_clock::now();
                    if(std::chrono::duration<double>(now-begin).count()>25) throw std::runtime_error("capture exceeded 25 seconds");
                    if(!sample) continue;
                    if(count==30) { first=now; firstStamp=stamp; }
                    if(count>=30) { last=now; lastStamp=stamp; }
                    ++count;
                }
                double seconds=std::chrono::duration<double>(last-first).count();
                std::cout << "{\"capture\":{\"fps\":" << 119/seconds << ",\"timestamp_fps\":" << (lastStamp>firstStamp?119e7/(lastStamp-firstStamp):0)
                    << ",\"frames\":120,\"compressed_samples\":true,\"images_saved\":false}}\n";
            }
            // SourceReader destruction may shut down the source. Restore while it is alive.
            // The launcher still verifies/restores through a fresh source after every trial.
            if(!controls.restore()) result=3;
        }
    } catch(const std::exception& e) { std::cerr << e.what() << "\n"; result=1; }
    MFShutdown(); CoUninitialize(); return result;
}
