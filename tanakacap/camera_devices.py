"""Enumerate DirectShow metadata only: never instantiate a capture filter."""
import ctypes as c
import os
import uuid


def enumerate_cameras():
    if os.name!='nt':return []
    ole=c.OleDLL('ole32')
    ole.CoInitializeEx.argtypes=[c.c_void_p,c.c_uint]
    result=ole.CoInitializeEx(None,2)
    initialized=result in (0,1)
    if result not in (0,1,-2147417850):raise OSError(result,'COM initialization failed')
    def guid(value):return (c.c_ubyte*16).from_buffer_copy(uuid.UUID(value).bytes_le)
    def call(pointer,index,*types):
        table=c.cast(pointer,c.POINTER(c.POINTER(c.c_void_p))).contents
        return c.WINFUNCTYPE(c.c_long,c.c_void_p,*types)(table[index])
    def release(p):
        if p:call(p,2)(p)
    device=c.c_void_p();enum=c.c_void_p();found=[]
    try:
        cls=guid('62BE5D10-60EB-11D0-BD3B-00A0C911CE86');iid=guid('29840822-5B84-11D0-BD3B-00A0C911CE86')
        ole.CoCreateInstance.argtypes=[c.c_void_p,c.c_void_p,c.c_ulong,c.c_void_p,c.POINTER(c.c_void_p)]
        hr=ole.CoCreateInstance(c.byref(cls),None,1,c.byref(iid),c.byref(device))
        if hr<0:raise OSError(hr,'Device enumeration unavailable')
        category=guid('860BB310-5D01-11D0-BD3B-00A0C911CE86')
        hr=call(device,3,c.c_void_p,c.POINTER(c.c_void_p),c.c_ulong)(device,c.byref(category),c.byref(enum),0)
        if hr==1:return []
        if hr<0:raise OSError(hr,'Camera enumeration failed')
        while True:
            moniker=c.c_void_p();fetched=c.c_ulong()
            if call(enum,3,c.c_ulong,c.POINTER(c.c_void_p),c.POINTER(c.c_ulong))(enum,1,c.byref(moniker),c.byref(fetched))!=0:break
            bag=c.c_void_p()
            try:
                bagid=guid('55272A00-42CB-11CE-8135-00AA004BB851')
                hr=call(moniker,9,c.c_void_p,c.c_void_p,c.c_void_p,c.POINTER(c.c_void_p))(moniker,None,None,c.byref(bagid),c.byref(bag))
                name='カメラ '+str(len(found))
                if hr>=0:
                    variant=c.create_string_buffer(24)
                    hr=call(bag,3,c.c_wchar_p,c.c_void_p,c.c_void_p)(bag,'FriendlyName',variant,None)
                    if hr>=0 and c.c_ushort.from_buffer(variant).value==8:
                        name=c.wstring_at(c.c_void_p.from_buffer(variant,8).value)
                    c.OleDLL('oleaut32').VariantClear(variant)
                found.append(dict(index=len(found),name=name))
            finally:release(bag);release(moniker)
        return found
    finally:
        release(enum);release(device)
        if initialized:ole.CoUninitialize()
