#!/usr/bin/env python3
"""Compare a stock kernel module's __versions table against our kernel's Module.symvers."""
import struct, sys, collections

MODVER = '<Q56s'  # struct modversion_info: unsigned long crc (u64 on arm64) + char name[MODULE_NAME_LEN=56]

def module_versions(path):
    with open(path,'rb') as f: data=f.read()
    if data[:4] != b'\x7fELF':
        raise ValueError("not ELF")
    is64 = data[4]==2
    if not is64: raise ValueError("32bit")
    e_shoff = struct.unpack_from('<Q', data, 0x28)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from('<3H', data, 0x3a)
    secs=[]
    for i in range(e_shnum):
        off=e_shoff+i*e_shentsize
        name,typ,flags,addr,offset,size,link,info,align,entsize=struct.unpack_from('<IIQQQQIIQQ',data,off)
        secs.append(dict(name=name,typ=typ,offset=offset,size=size))
    shstr=secs[e_shstrndx]
    def sname(n):
        end=data.index(b'\0', shstr['offset']+n)
        return data[shstr['offset']+n:end].decode(errors='replace')
    out={}
    for s in secs:
        nm=sname(s['name'])
        if nm=='__versions':
            n=s['size']//struct.calcsize(MODVER)
            vers=[]
            for i in range(n):
                crc,nb=struct.unpack_from(MODVER,data,s['offset']+i*struct.calcsize(MODVER))
                name=nb.split(b'\0')[0].decode(errors='replace')
                if name: vers.append((name,hex(crc)))
            out=vers
    return out

def symvers(path):
    d=collections.defaultdict(list)
    for line in open(path):
        parts=line.split()
        if len(parts)>=2: d[parts[1]].append(parts[0])
    return d

if __name__=='__main__':
    ko=sys.argv[1]; symv=sys.argv[2] if len(sys.argv)>2 else '/workspace/build/star-susfs-int/Module.symvers'
    ours=symvers(symv)
    vers=module_versions(ko)
    print(f"module declares {len(vers)} versioned symbols")
    ok=bad=missing=0; badlist=[]
    for name,crc in vers:
        have=ours.get(name)
        if not have:
            missing+=1; badlist.append((name,crc,'MISSING_IN_KERNEL'))
        elif crc in have:
            ok+=1
        else:
            bad+=1; badlist.append((name,crc,'CRC_DIFF:'+','.join(have)))
    print(f"MATCH: {ok}   DIFF: {bad}   MISSING: {missing}")
    if badlist:
        print("---- sample mismatches (first 25) ----")
        for name,crc,why in badlist[:25]:
            print(f"  {name:44} module={crc:12} {why}")
