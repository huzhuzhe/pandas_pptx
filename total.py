#-*- coding:utf-8 -*-
#"2018年1月26日"

from pandas_pptx import public as p
from connect.connect import dwsql,wesql,pd,close

# 本章的数据不需要单独跑，在to_pptx中就可以跑出来了


# 1.获取商户的名称
name='''select bid ,bbrandname from welife_bizs where bid=%i'''  %p.bid
named=wesql(name)
sname=named.ix[0,'bbrandname']


# 2.商户的总的会员存量
cunliang='''select count(uid) as num
from welife%s.welife_users%s t
left join welife_card_categories s on t.ccid = s.ccid
where t.bid=%i''' %(p.dbs,p.tbs,p.bid)
print('total_存量')
cunliang_d=wesql(cunliang)

cunliang_d_num=cunliang_d.ix[0,'num']



# 3.会员总的消费金额
# 1.2累计消费金额和次数
consume_total='''select sum(tcTotalFee)/100 'total_money'
from dprpt_welife_trade_consume_detail 
where bid=%i
and ftime>=%s
and ftime<%s
and tctype=2''' %(p.bid,p.ftime_s,p.ftime_e)
print('total_消费金额')
consume_total=dwsql(consume_total)
consume_total_num=consume_total.ix[0,'total_money']
    
# 1.3回头客累计消费金额各次数 
consume_second='''select 
-- sum(trade_num) '回头客累计消费次数',
sum(trade_money) 'total_money_second'
from (select uid,count(1) trade_num,sum(tctotalfee)/100 trade_money 
from dprpt_welife_trade_consume_detail
where bid=%i
and tctype=2 
and ftime>=%s
and ftime<%s
group by uid) a
where trade_num>=2''' %(p.bid,p.ftime_s,p.ftime_e)
print('total_回头客')
consume_second=dwsql(consume_second)
consume_second_num=consume_second.ix[0,'total_money_second']


# 1.4营销消费
ladong='''select sum(拉动现金消费) as '拉动现金消费',sum(拉动券消费) as '拉动券消费',sum(拉动储值消费) as '拉动储值消费'
from 
(select aid '活动编号',
activityname '活动名称',
couponname '券名称',
sum(couponsendsum) '发券量',
sum(couponusedsum) '使用券量',
sum(tradecash - cancelcash)/100 '拉动现金消费',
sum(camount * couponusedsum)/100 '拉动券消费',
sum(tradeprepay - canceltradepv)/100 '拉动储值消费',
concat(round(100*sum(couponusedsum)/sum(couponsendsum),2),'%%') '使用率'
from dprpt_welife_activity_log 
where ftime>%s and ftime<%s and bid=%i
group by activityname,couponname) a ''' %(p.ftime_s,p.ftime_e,p.bid)
print('total_营销')
ladong_d=dwsql(ladong)
ladong_d['total_market']=ladong_d['拉动现金消费']+ladong_d['拉动券消费']+ladong_d['拉动储值消费']
ladong_d_num=ladong_d.ix[0,'total_market']


# 4.储值金额(tcChargeType是19的话就是账户合并，如果是储值余额的话，19之后会自动清零，但是储值记录还在里面）
charge_total='''select 
sum(c.tcsale/100) '储值金额实收',count(c.uid) '储值次数',count(distinct(c.uid)) '储值人数'
from welife_trade_charges c 
where c.tccreated >=%s  and  c.tccreated < %s and  c.bid=%i
and c.tcStatus=1 and tcChargeType<>19 and tctype=1 ''' %(p.ftime_s,p.ftime_e,p.bid)
print('total_储值')
charge_total_d=wesql(charge_total)


# 4.1储值消耗
charge_consume='''select
(sum(case when tctype in (2,8) then tclprinciple/100 end) - sum(case when tctype=3 then tclprinciple/100 end)) '储值消耗'
from dprpt_welife_trade_consume_detail
where  ftime>=%s and ftime<%s and  bid=%i ''' %(p.ftime_s,p.ftime_e,p.bid)
print('total_储值消耗')
charge_consume_d=dwsql(charge_consume)
charge_num=pd.concat([charge_total_d,charge_consume_d],axis=1)
charge_num['储值沉淀']=charge_num['储值金额实收']-charge_num['储值消耗']

charge_total_money=charge_num.ix[0,'储值金额实收']
charge_saving=charge_num.ix[0,'储值沉淀']

















