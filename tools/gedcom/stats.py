import sys,re,collections
lines=open(sys.argv[1],encoding='utf-8-sig').read().splitlines()
recs=[];cur=None
for l in lines:
    m=re.match(r'(\d+) (\S+)(?: (.*))?$',l)
    if not m: continue
    lv,tag,val=int(m[1]),m[2],m[3] or ''
    if lv==0: cur={'id':tag,'type':val or tag,'lines':[]};recs.append(cur)
    else: cur['lines'].append((lv,tag,val))
indi=[r for r in recs if r['type']=='INDI']
years=[];plac=collections.Counter();nodate=0;nosour=0;living=0;deathless=0
for r in indi:
    L=r['lines']; ev=None;b=None;hasdeat=False;hs=False
    for lv,t,v in L:
        if lv==1: ev=t
        if lv==1 and t=='DEAT': hasdeat=True
        if t=='SOUR': hs=True
        if lv==2 and t=='DATE' and ev=='BIRT':
            m=re.search(r'(\d{4})',v); b=int(m[1]) if m else None
        if lv==2 and t=='PLAC': plac[v]+=1
    if b: years.append(b)
    else: nodate+=1
    if not hs: nosour+=1
    if not hasdeat and (b is None or b>1926): living+=1
years.sort()
print('osob',len(indi),'s rokem narozeni',len(years),'bez',nodate)
print('rozsah',years[0],years[-1]); 
dec=collections.Counter((y//50)*50 for y in years); print('po 50 letech',sorted(dec.items()))
print('osob bez jakekoli citace',nosour,'pravdep. zijicich',living)
print('unikatnich mist',len(plac)); print('top mista',plac.most_common(25))
# citation PAGE / TEXT samples by source type
src={r['id']:dict((t,v) for lv,t,v in r['lines'] if lv==1) for r in recs if r['type']=='SOUR'}
for k,v in src.items(): print(k,v.get('_TYPE'),'|',v.get('TITL'))
