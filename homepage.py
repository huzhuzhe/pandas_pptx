#-*- coding:utf-8 -*-
#"2018年3月20日"

print('================')
print('homepage')
print('================')

from connect.connect import close,pd,wesql,dwsql
from pandas_pptx import public as p
import numpy as np 


# 1.总的存量和各等级的存量
huiyuan_new_create_grid='''select grid,sum(num) as new_create from(select
IFNULL(s.ccName,'%s') as 'grid',  
date_format(t.uRegistered, '%%Y%%m') as 'month',
count(1) num
from welife%s.welife_users%s t
left join welife_card_categories s on t.ccid = s.ccid
where t.bid =%i
-- and t.uRegistered >= %s
and t.uRegistered < %s
-- and t.uCardStatus=2
group by s.ccName,date_format(t.uRegistered,'%%Y%%m'))a group by grid'''  %(p.myname,p.dbs,p.tbs,p.bid,p.ftime_s,p.ftime_e)

print('1存量')
huiyuan_new_create_grid_d=wesql(huiyuan_new_create_grid)
# print(huiyuan_new_create_grid_d.head())
num_order=huiyuan_new_create_grid_d.sort_values(by=['new_create'],ascending=False)
new_index=np.arange(len(num_order))
num_order2=num_order.set_index(new_index)
# print(num_order2)

# 将各等级的会员拆分为两部分，其一是数量最多的前三个等级，其二是后面的几个等级归为其他类
if len(num_order2)>3:
    other_vip=num_order2.ix[3:,:]
    other_total=other_vip['new_create'].sum()
elif len(num_order2)==1:
    newpd=pd.DataFrame({'grid':'需要删除','new_create':0},index=[1,2])
    num_order2=pd.concat([num_order2,newpd])
    other_total=0
elif len(num_order2)==2:
    newpd=pd.DataFrame({'grid':'需要删除','new_create':0},index=[2])
    num_order2=pd.concat([num_order2,newpd])  
    other_total=0
else:
    other_total=0
total_num=huiyuan_new_create_grid_d['new_create'].sum()
# print(num_order2)
# close()


# 2.消费次数
#首次消费金额以及次数(用10元过滤掉单独核销券的消费）
consume_num_grid_first='''select  date_format(ftime,'%%Y%%m') as month ,
sum(fee) '首次消费金额' ,count(uid) as 首次消费次数,count(distinct(uid)) as 首次消费人数
from (select uid,grid,tcTotalFee/100 fee,min(tclcreated) ftime
from dprpt_welife_trade_consume_detail 
where 
-- ftime>=%s and 
ftime<%s and bid=%i
and tctype=2
and tcTotalFee>10000
group by uid) a                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
group by month''' %(p.ftime_s,p.ftime_e,p.bid)
consume_num_grid_first_d=dwsql(consume_num_grid_first)

# 总消费次数
consume_num_grid='''select date_format(ftime,'%%Y%%m') as month,
sum(tctotalfee/100) '消费金额',count(1) '消费次数',
count(distinct(uid)) '消费人数'
from dprpt_welife_trade_consume_detail 
where 
-- ftime>%s and 
ftime<%s and bid=%i 
and tctype=2
and tcTotalFee>10000
group by month''' %(p.ftime_s,p.ftime_e,p.bid)
consume_num_grid_d=dwsql(consume_num_grid)
re1=pd.merge(consume_num_grid_d,consume_num_grid_first_d,on='month')
re1['再次消费次数']=re1['消费次数']-re1['首次消费次数']
re2=re1[['消费次数','首次消费次数','再次消费次数']]
# print('re2',re2)
re3=re2.sum()
# print('消费次数')
# print(re3['消费次数'])



# 3.储值
# -----------储值金额实收
charge_tcsale='''select date_format(c.tccreated,'%%Y%%m') month,
sum(c.tcsale/100) '储值金额实收'
from welife_trade_charges c 
where c.bid=%i  and 
-- c.tccreated >= %s and  
c.tccreated < %s   
and tcChargeType <> 19
and c.tcStatus=1 and tcType=1 
group by month''' %(p.bid,p.ftime_s,p.ftime_e)
charge_tcsale_d=wesql(charge_tcsale)
if charge_tcsale_d.empty:
    charge_tcsale_d=pd.DataFrame({'month':'201601','储值金额实收':100},index=[0])

#-----------储值金额消耗
charge_consume='''select date_format(ftime,'%%Y%%m') month,
sum(case when tctype in (2,8) then tclprinciple/100 end) - ifnull(sum(case when tctype=3 then tclprinciple/100 end),0) '储值实收消耗'
from dprpt_welife_trade_consume_detail
where 
-- ftime>=%s and
ftime<%s 
and bid=%i
group by month''' %(p.ftime_s,p.ftime_e,p.bid)
charge_consume_d=dwsql(charge_consume)
if charge_consume_d.empty:
    charge_consume_d=pd.DataFrame({'month':'201701','储值实收消耗':0},index=[0])
charge_consume_d.fillna(0,inplace=True)
re5=pd.merge(charge_tcsale_d,charge_consume_d,on='month')
re5['储值沉淀']=re5['储值金额实收']-re5['储值实收消耗']
if re5.empty:
    re5=pd.DataFrame({'储值金额实收':0,'储值实收消耗':0,'储值沉淀':0},index=[0])
re6=re5.sum()


re6=re5[['储值金额实收','储值实收消耗','储值沉淀']].sum().apply(lambda x:int(x))

# close()




# 4.积分
# 积分的使用人数(这里是依照grid分组求的，做图时候可以只算全部的使用率)
point_use_grid='''select count(distinct(case when a.sendpoint > 0 then a.uid end)) '积分发放人数',
count(distinct(case when pointpay > 0  then a.uid end)) '积分使用人数'
-- ,concat(round(100*count(distinct(case when a.pointpay > 0 then a.uid end))/count(distinct(a.uid)),2),'%%') '使用积分抵扣占比'
from dprpt_welife_trade_consume_detail a
where bid=%i
and tctype=2 
-- and ftime>=%s
and ftime<%s ''' %(p.bid,p.ftime_s,p.ftime_e)
print('2.积分使用人数')
point_use_grid_d=dwsql(point_use_grid)
psendnum=point_use_grid_d.ix[0,'积分发放人数']
pusednum=point_use_grid_d.ix[0,'积分使用人数']
# print(point_use_grid_d)


#积分的使用数量
point_use_number='''select  
sum(case when t.tctradetype = 1 then t.tccredit end) 发放积分,
sum(case when t.tctradetype = 2 then t.tccredit end) 使用积分
-- concat(round(100*sum(case when t.tctradetype = 2 then t.tccredit end)/sum(case when t.tctradetype = 1 then t.tccredit end),2),'%%') '积分消耗占比'
from welife_trade_credit t
where bid=%i
-- and tcCreated >= %s
and tcCreated < %s ''' %(p.bid,p.ftime_s,p.ftime_e)
print('3.积分使用数量')
point_use_number_d=wesql(point_use_number)
point_use_number_d.fillna(0,inplace=True)
nsendnum=point_use_number_d.ix[0,'发放积分']
nusednum=point_use_number_d.ix[0,'使用积分']
# print(point_use_number_d)



# 折扣力度
zhekoulidu='''select  sum(tctotalfee)/100 as 消费总金额,sum(tcfee)/100 as  消费实收现金,
sum(tclprinciple)/100 as '消费使用储值本金' from 
dprpt_welife_trade_consume_detail 
where 
-- ftime>%s and 
ftime<%s and  bid=%i and tctype=2''' %(p.ftime_s,p.ftime_e,p.bid)

zhekoulidu_d=dwsql(zhekoulidu)
zhekoulidu_d['折扣力度']=(zhekoulidu_d['消费实收现金']+zhekoulidu_d['消费使用储值本金'])/zhekoulidu_d['消费总金额']
# print('折扣力度')
print(zhekoulidu_d)
zhekou=zhekoulidu_d.ix[0,'折扣力度']



# 取关人数
cancle_user='''select 
count(distinct(uid)) as cancle_num
from welife%s.welife_users%s t
where t.bid =%i  and t.uCardStatus=3
-- and uRegistered>=%s
and uRegistered<%s'''  %(p.dbs,p.tbs,p.bid,p.ftime_s,p.ftime_e)
cancle_user_d=wesql(cancle_user)
# print('取关人数')
print(cancle_user_d)
c_num=cancle_user_d.ix[0,'cancle_num']






# close()
