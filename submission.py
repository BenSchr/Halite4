
from random import choice
from pprint import pprint
import numpy as np
import seaborn as sns
import math

def toMetanum(num,boardradius=21):
    metanum=boardradius*boardradius*3+boardradius+(boardradius*2)*math.floor(num/boardradius)+num
    return metanum

def position(num):
    x=num%21
    y=num//21
    return (y,x)

def metaposition(meta,nometa=True):
    if nometa: meta=toMetanum(meta)
    x=meta%(21*3)
    y=meta//(21*3)
    return(y,x)

# def around(num,radius):
#     l=[] 
#     metaboard=np.tile(np.reshape(range(0,21*21),(21,21)),(3,3)).reshape(-1)
#     metanum=441*3+21+(21*2)*math.floor(num/21)+num
#     leftouter=metanum-(21*3)*radius-radius
#     for i in range(0,radius*2+1):
#         left=leftouter+21*3*i
#         l.append(metaboard[left])
#         for j in range(1,radius*2+1):
#             l.append(metaboard[left+j])
    
#     l.remove(num) 

#     return l

def around(num,radius):
    l=[] 
   
    metanum=toMetanum(num)
  
    leftouter=metanum-(21*3)*radius-radius
    for i in range(0,radius*2+1):
        left=leftouter+21*3*i
        l.append(left)
        for j in range(1,radius*2+1):
            l.append(left+j)
   
    l.remove(metanum) 
    
    return l

def maxhalite(obs,num,radius,controls,metaboard):
    
    try:
       
        player=metaposition(num)
     
        l = around(num,radius)
    
        l = [x for x in l if metaboard[x] not in controls["blockedMining"]]
      
        halite=[]
        
        #metahalite=obs.halite*9
        metahalite=np.tile(np.reshape(obs.halite,(boardradius,boardradius)),(3,3)).reshape(-1)
        
        for field in l:
            org_h=metahalite[field]
            mpos=metaposition(field,nometa=False)
            dist = math.sqrt(abs(mpos[1] - player[1]) + abs(mpos[0] - player[0])) 
            #print(dist)
            halite.append(float(org_h)/float(dist))
        #halite=[obs.halite[x] for x in l]
        maxh = l[halite.index(max(halite))]
        
        return maxh
    
    except Exception as e: 
        print(e)
        return 0
    

def getCompass(o_x,o_y,d_x,d_y):
    o_y=o_y*-1
    d_y=d_y*-1
    
    delta_x=d_x-o_x
    delta_y=d_y-o_y

    degrees = math.atan2(delta_x, delta_y)/math.pi*180
    
    alt=[degrees,degrees+90,degrees-90]
    
    for i,a in enumerate(alt):
        if a < 0:
            alt[i]=a+360

    directions=[["NORTH"],["NORTH","EAST"],["EAST"],["SOUTH","EAST"],["SOUTH"],["SOUTH","WEST"],["WEST"],["NORTH","WEST"],["NORTH"]]

    return directions[round(alt[0]/45)],directions[round(alt[1]/45)],directions[round(alt[2]/45)]   

def nextdirection(meta_cur,meta_to,controls,metaboard,boardradius=21):

    meta_p_cur=metaposition(meta_cur,nometa=False)
    meta_p_to=metaposition(meta_to,nometa=False)

    org_cur=metaboard[meta_cur]
    org_to=metaboard[meta_to]
    ddict={}
    ddict["NORTH"]=org_cur-boardradius
    ddict["SOUTH"]=org_cur+boardradius
    ddict["EAST"]=org_cur+1
    ddict["WEST"]=org_cur-1
    ddict["METANORTH"]=meta_cur-boardradius*3
    ddict["METASOUTH"]=meta_cur+boardradius*3
    ddict["METAEAST"]=meta_cur+1
    ddict["METAWEST"]=meta_cur-1
    
    prio,alt1,alt2=getCompass(meta_p_cur[1],meta_p_cur[0],meta_p_to[1],meta_p_to[0])
    
    alt=alt1+alt2
    
    for d in prio:
        #print(f"Trying {d}")
        if ddict[d] in controls["blockedMoving"]+controls["blockedCurMining"]:
            #print(f"Blocked {d}")
            continue
        else:
            controls["blockedMoving"].append(ddict[d])
            #print(f"Choosing {d}")
            return d,ddict["META"+d]
    
    for d in prio:
        #print(f"Trying {d}")
        if ddict[d] in controls["blockedMoving"]:
            #print(f"Waiting {d}")
            return None,meta_cur
            
    for d in alt:
        if ddict[d] in controls["blockedMoving"]+controls["blockedCurMining"]:
            #print(f"Blocked {d}")
            continue
        else:
            controls["blockedMoving"].append(ddict[d])
            #print(f"Choosing {d}")
            return d,ddict["META"+d]
        
    return None,meta_cur


controls={}
controls["ships"]={}#ID,State(Mining,Moving,Deploying,Converted),CurPos,MovingTo
controls["blockedShipPos"]=[]
controls["blockedMoving"]=[]
controls["blockedMining"]=[]
controls["blockedCurMining"]=[]
controls["destroyedShips"]=[]
controls["convertedShips"]=[]

boardradius=21

metaboard=np.tile(np.reshape(range(0,boardradius*boardradius),(boardradius,boardradius)),(3,3)).reshape(-1)

def agent(obs):
    action = {}
    
    #logger(obs)
    
    print(controls)
    
    radius = 10
    
    controls["blockedShipPos"]=[]
    controls["blockedMoving"]=[]
           
    
    print(f"####### STEP {obs.step} ########")
    
    my_shipyards=obs.players[0][1]
    my_ships=obs.players[0][2]
    
    #Check for new Ships
    for ship_id in my_ships:
        ship_pos=my_ships[ship_id][0]
        if ship_id not in controls["ships"].keys():
            controls["ships"][ship_id]={}
            controls["ships"][ship_id]["state"]="idle"
            controls["ships"][ship_id]["CurPos"]=ship_pos
            controls["ships"][ship_id]["MetaPos"]=toMetanum(ship_pos)
        
    #Check for new destroyed ships
    for x in controls["ships"].keys():
        if x not in controls["destroyedShips"]+controls["convertedShips"]:
            if x not in my_ships.keys():
                controls["ships"][x]["state"]="destroyed"
                controls["destroyedShips"].append(x)
                try: controls["blockedMining"].remove(controls["ships"][x]["movingTo"])
                except: print(Exception)

    print(f"Ships: {controls['ships']}")
    
    for ship_id in my_ships:
        ship_pos=my_ships[ship_id][0]
        controls["ships"][ship_id]["CurPos"]=ship_pos
        mship_pos=controls["ships"][ship_id]["MetaPos"]
        print(f"My ShipID is {ship_id} and I'm at {ship_pos} My State is {controls['ships'][ship_id]['state']}")
        
        #IDLE
        if controls["ships"][ship_id]["state"]=="idle":
            
            #Find MiningSpot
            mSpot = maxhalite(obs,ship_pos,radius,controls,metaboard)
            controls["blockedMining"].append(metaboard[mSpot])
            controls["ships"][ship_id]["state"]="move_mining"
            controls["ships"][ship_id]["movingTo"]=metaboard[mSpot]
            controls["ships"][ship_id]["metaTo"]=mSpot
#             nextd,nextmeta=nextdirection(mship_pos,mSpot,controls,metaboard)
#             if nextd !=None:
#                 action[ship_id]=nextd
#             controls["ships"][ship_id]["MetaPos"]=nextmeta
            
        #Check for next Step
        if controls["ships"][ship_id]["state"]=="move_mining":
            if controls["ships"][ship_id]["CurPos"]==controls["ships"][ship_id]["movingTo"]:
                controls["ships"][ship_id]["state"]=="mining"
                controls["blockedCurMining"].append(ship_pos)
            else:
                meta_mSpot=controls["ships"][ship_id]["metaTo"]
                nextd,nextmeta=nextdirection(mship_pos,meta_mSpot,controls,metaboard)
                if nextd !=None:
                    action[ship_id]=nextd
                controls["ships"][ship_id]["MetaPos"]=nextmeta
        
        if controls["ships"][ship_id]["state"]=="mining":
            action[ship_id]=None
        
        if obs.step==0:
            action[ship_id] = "CONVERT"
            controls["convertedShips"].append(ship_id)
            controls["ships"][ship_id]["state"]="converted"
            try: controls["blockedMining"].remove(controls["ships"][x]["movingTo"])
            except: print(Exception)
                
    for sy_id in my_shipyards:
        if len(my_ships)<10 and obs.players[0][0]>500:
            if obs.players[0][1][sy_id] not in controls["blockedMoving"]:
                action[sy_id]="SPAWN"   
                
    return action
