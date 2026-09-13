"""Windows Media Foundation/KS controls; metadata enumeration never activates devices.

No capture reader, preview, audio, third-party DLL or device-name heuristics.
"""
import ctypes as c
from contextlib import contextmanager
import os
import re
import uuid


def guid(value):
    return (c.c_ubyte*16).from_buffer_copy(uuid.UUID(value).bytes_le)


def call(pointer, index, *types):
    table=c.cast(pointer,c.POINTER(c.POINTER(c.c_void_p))).contents
    return c.WINFUNCTYPE(c.c_long,c.c_void_p,*types)(table[index])


def check(hr, operation):
    if hr<0:raise OSError(hr, operation+' (HRESULT 0x%08X)'%(hr & 0xffffffff))


def release(pointer):
    if pointer:call(pointer,2)(pointer)


@contextmanager
def foundation():
    if os.name!='nt':raise OSError('Windows camera controls are unavailable')
    ole=c.WinDLL('ole32'); mf=c.WinDLL('mfplat')
    ole.CoInitializeEx.argtypes=[c.c_void_p,c.c_ulong]
    hr=ole.CoInitializeEx(None,0)
    if hr not in (0,1,-2147417850):check(hr,'CoInitializeEx')
    initialized=hr in (0,1)
    started=False
    try:
        check(mf.MFStartup(0x00020070,0),'MFStartup');started=True
        yield ole,mf
    finally:
        if started:mf.MFShutdown()
        if initialized:ole.CoUninitialize()


@contextmanager
def activations():
    with foundation() as (ole,mf):
        attrs=c.c_void_p();items=c.POINTER(c.c_void_p)();count=c.c_uint()
        mf.MFCreateAttributes.argtypes=[c.POINTER(c.c_void_p),c.c_uint]
        api=c.WinDLL('mf')
        api.MFEnumDeviceSources.argtypes=[c.c_void_p,c.POINTER(c.POINTER(c.c_void_p)),c.POINTER(c.c_uint)]
        ole.CoTaskMemFree.argtypes=[c.c_void_p]
        try:
            check(mf.MFCreateAttributes(c.byref(attrs),1),'MFCreateAttributes')
            key=guid('c60ac5fe-252a-478f-a0ef-bc8fa5f7cad3')
            value=guid('8ac3587a-4ae7-42d8-99e0-0a6013eef90f')
            check(call(attrs,24,c.c_void_p,c.c_void_p)(attrs,c.byref(key),c.byref(value)),'Video device attribute')
            check(api.MFEnumDeviceSources(attrs,c.byref(items),c.byref(count)),'MFEnumDeviceSources')
            yield [c.c_void_p(items[i]) for i in range(count.value)],ole
        finally:
            if items:
                for i in range(count.value):release(c.c_void_p(items[i]))
                ole.CoTaskMemFree(items)
            release(attrs)


def string_attr(pointer, key, ole):
    key=guid(key);value=c.c_void_p();length=c.c_uint()
    try:
        check(call(pointer,13,c.c_void_p,c.POINTER(c.c_void_p),c.POINTER(c.c_uint))(
            pointer,c.byref(key),c.byref(value),c.byref(length)),'Camera identity')
        return c.wstring_at(value)
    finally:
        if value:ole.CoTaskMemFree(value)


def metadata(pointer, index, ole):
    return dict(index=index,
                name=string_attr(pointer,'60d0e559-52f8-4fa2-bbce-acdb34a8ec01',ole),
                device_id=string_attr(pointer,'58f0aad8-22bf-4f8a-bb3d-d2c4978c6e2f',ole))


def enumerate_mf_cameras():
    with activations() as (items,ole):
        return [metadata(p,i,ole) for i,p in enumerate(items)]


def identity_key(device_id):
    # DSHOW capture and MF video-camera interface class GUIDs differ. Keep the
    # complete PnP instance and pin suffix; VID/PID or friendly name alone is unsafe.
    return re.sub(r'#\{(?:65e8773d-8f56-11d0-a3b9-00a0c9223196|e5323777-f976-4f5b-9b55-b94699c46e44)\}',
                  '#{video-interface}', device_id.casefold())


class Property(c.Structure):
    _fields_=[('set',c.c_ubyte*16),('id',c.c_ulong),('flags',c.c_ulong)]


class ProcAmp(c.Structure):
    _fields_=[('property',Property),('value',c.c_long),('flags',c.c_ulong),('capabilities',c.c_ulong)]


@contextmanager
def media_source(device_id):
    """Resolve the exact symbolic link, activate only that video device, and close it."""
    if not device_id:raise OSError('No stable camera identity; control was not changed')
    with activations() as (items,ole):
        matches=[p for i,p in enumerate(items) if identity_key(metadata(p,i,ole)['device_id'])==identity_key(device_id)]
        if len(matches)!=1:raise OSError('Camera identity could not be matched across APIs; control was not changed')
        source=c.c_void_p()
        try:
            iid=guid('279a808d-aec7-40c8-9c6b-a6b492c78a66') # IMFMediaSource
            check(call(matches[0],33,c.c_void_p,c.POINTER(c.c_void_p))(matches[0],c.byref(iid),c.byref(source)),'Activate video device')
            yield source
        finally:
            if source:call(source,12)(source)
            release(source)
            if source:call(matches[0],34)(matches[0])


@contextmanager
def power_control(device_id, kind='powerline'):
    with media_source(device_id) as source:
        ks=c.c_void_p()
        try:
            iid=guid('28f54685-06fd-11d2-b27a-00a0c9223196')
            check(call(source,0,c.c_void_p,c.POINTER(c.c_void_p))(source,c.byref(iid),c.byref(ks)),'Camera KS controls unsupported')
            def access(value=None, flags=0, *, property_id=None):
                request=ProcAmp()
                request.property.set=guid('c6e13360-30ac-11d0-a18c-00a0c9118956' if kind=='powerline' else 'c6e13370-30ac-11d0-a18c-00a0c9118956')
                request.property.id=property_id if property_id is not None else (13 if kind=='powerline' else 19)
                request.property.flags=1 if value is None else 2 # GET / SET
                request.value=0 if value is None else value;request.flags=flags
                returned=c.c_ulong()
                check(call(ks,3,c.c_void_p,c.c_ulong,c.c_void_p,c.c_ulong,c.POINTER(c.c_ulong))(
                    ks,c.byref(request),c.sizeof(request),c.byref(request),c.sizeof(request),c.byref(returned)),
                    'Powerline read' if value is None else 'Powerline write')
                return request.value,request.flags
            yield access
        finally:
            release(ks)


def native_modes(device_id):
    """Inspect supported combinations, without reading frames or starting a renderer."""
    with media_source(device_id) as source:
        reader=c.c_void_p();api=c.WinDLL('mfreadwrite')
        api.MFCreateSourceReaderFromMediaSource.argtypes=[c.c_void_p,c.c_void_p,c.POINTER(c.c_void_p)]
        try:
            check(api.MFCreateSourceReaderFromMediaSource(source,None,c.byref(reader)),'Create mode reader')
            modes=[]
            for index in range(4096):
                media=c.c_void_p()
                hr=call(reader,5,c.c_ulong,c.c_ulong,c.POINTER(c.c_void_p))(reader,0xfffffffc,index,c.byref(media))
                if hr & 0xffffffff==0xc00d36b9:break # MF_E_NO_MORE_TYPES
                check(hr,'Enumerate native mode')
                try:
                    values=[]
                    for key in ('1652c33d-d6b2-4012-b834-72030849a37d','c459a2e8-3d2c-4e44-b132-fee5156c7bb0'):
                        key=guid(key);value=c.c_ulonglong()
                        check(call(media,8,c.c_void_p,c.POINTER(c.c_ulonglong))(media,c.byref(key),c.byref(value)),'Mode attribute')
                        values.append((value.value>>32,value.value & 0xffffffff))
                    key=guid('f7e34c9a-42e8-4714-b74b-cb29d72c35e5');subtype=(c.c_ubyte*16)()
                    check(call(media,10,c.c_void_p,c.c_void_p)(media,c.byref(key),c.byref(subtype)),'Mode subtype')
                    width,height=values[0];num,den=values[1]
                    if not den:continue
                    modes.append(dict(width=width,height=height,fps=num/den,fourcc=int.from_bytes(bytes(subtype)[:4],'little')))
                finally:release(media)
            return modes
        finally:release(reader)


class WindowsPowerline:
    def __init__(self, device_id, kind='powerline'):
        if kind not in ('powerline','lowlight'):raise ValueError('Unknown camera control')
        self.device_id=device_id;self.kind=kind
    def read(self):
        with power_control(self.device_id,self.kind) as access:
            if self.kind=='lowlight' and not access(property_id=4)[1] & 1:
                raise OSError('暗所補正は自動露出時のみ有効です。露出モードは変更していません。')
            return access()
    def write(self, value, flags):
        with power_control(self.device_id,self.kind) as access:
            access(value,flags)
            return access()
