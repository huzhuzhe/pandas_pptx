#-*- coding:utf-8 -*-
#"2018年1月6日"

from connect.connect import dwsql,wesql,pd,close
import matplotlib.pyplot as plt 
from  datetime import datetime
import numpy as np
from pandas_pptx import public as p
from pandas_pptx.method_old import bar_h,line_h,autolabel,bar_h2,xuanf,xuanf1,xuanf2,bar_h3,to_days,autolabel2,double_line2,autolabel_size
# from matplotlib.ticker import FuncFormatter


print('=========================')
print('consume')



plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号

# 获取等级
ccname='''select ccid as grid,ccname from welife_card_categories where bid=%i
-- and ccid in (3006675,3006902)
''' %p.bid
ccname_d=wesql(ccname)
cate=ccname_d.ix[:,'ccname']




# 1.每月整体的营业额
consume_money=''' select  date_format(ftime,'%%Y%%m') as month,count(uid) as 消费次数,count(distinct(uid)) as 消费人数,
sum(tctotalfee/100) as 消费金额
from dprpt_welife_trade_consume_detail 
where bid=%i and tctype=2 and  ftime>=%s and ftime<%s 
group by date_format(ftime,'%%Y%%m') ''' %(p.bid,p.ftime_s,p.ftime_e)

print('1计算每月的全部营业额')
consume_money_d=dwsql(consume_money)
# 画图的时候，按照横坐标已经自动的groupby
bar_h(13,consume_money_d['month'],consume_money_d['消费金额'],'每月会员整体营业额')

# 2.首次消费和再次消费的情况
consume_firsttime_money='''select date_format(mintime,'%%Y%%m') 'month',
count(uid) as '首次消费次数',count(distinct(uid)) as 消费人数,sum(fee) '首次消费金额' 
from (select uid,tcTotalFee/100 fee,min(tclcreated) mintime
from dprpt_welife_trade_consume_detail 
where bid=%i
and ftime<%s
and tctype=2
group by uid) a
group by date_format(mintime,'%%Y%%m')''' %(p.bid,p.ftime_e)
print('2计算首次消费金额')
consume_firsttime_money_d=dwsql(consume_firsttime_money)
# 算出再次消费金额
re1=pd.merge(consume_money_d,consume_firsttime_money_d,on='month',how='left')
re1['再次消费金额']=re1['消费金额']-re1['首次消费金额']
re1=re1.fillna(0)
# print(re1.head())
alist=['首次消费金额','再次消费金额']
# line_h(14,re1['month'],re1['首次消费金额'],re1['再次消费金额'],'首次消费金额','再次消费金额','消费金额的构成')
double_line2(14, re1['month'], re1, '月份', '消费金额', alist, '消费金额的构成')





# 3.各等级的营业额
consume_num_grid='''select month as  '月份',
ggrid as grid,
fee as '消费金额',
num as '消费次数',
nup as  '消费人数'
from (
select date_format(ftime,'%%Y%%m') as month,
if(grid=0,'%s',grid) ggrid ,
sum(tctotalfee/100) fee,
count(1) num ,count(distinct(uid)) nup 
from dprpt_welife_trade_consume_detail 
where  ftime>%s and ftime<%s  and bid=%i 
and tctype=2 

-- and grid in (3004945,3007787,3009255,3007788,3007789)

group by month,ggrid) a  ''' %(p.myccid,p.ftime_s,p.ftime_e,p.bid)

print('3计算各等级的消费金额')
consume_num_grid_d1=dwsql(consume_num_grid)
# print(consume_num_grid_d1)
consume_num_grid_d1['grid']=consume_num_grid_d1['grid'].apply(lambda x:str(x))
ccname_d['grid']=ccname_d['grid'].apply(lambda x:str(x))
consume_num_grid_d=pd.merge(consume_num_grid_d1,ccname_d,on='grid')
# print(consume_num_grid_d)
re1=pd.pivot_table(consume_num_grid_d,index='ccname',values='消费次数',aggfunc=np.mean).reset_index()
# print(re1.head())
re1_new_i=np.arange(len(re1))
# print(re1_new_i)
# 万一re1的行数很少的话，取前两行
# print(re1.head())
if len(re1)>3:
    re1_sort=re1.sort_values(by='消费次数',ascending=False).set_index(re1_new_i).head(3)
else:
    re1_sort=re1.sort_values(by='消费次数',ascending=False).set_index(re1_new_i).head(2)


# 只有将等级的名称列表化之后，才能在下面添加标签的时候，有选择性的添加前面3个等级的标签 
my_cate=list(re1_sort.ix[:,'ccname'])
consume_num_grid_d_pivot_table=pd.pivot_table(consume_num_grid_d,index='月份',columns='ccname',values='消费金额',aggfunc=np.sum).reset_index()
name_list=list(set(consume_num_grid_d['ccname']))
# print(name_list)
# d_name=[]
# for i in name_list:  有几个等级不想添加标签，所以去除了这些等级
#     if not i in ['小厨粉','积分金卡','积分白金卡']:
#         d_name.append(i)
double_line2(15, consume_num_grid_d_pivot_table['月份'], consume_num_grid_d_pivot_table,
             '月份', '消费金额(单位：元)', name_list, '各等级会员消费金额')


# 计算各等级的桌均
re3=consume_num_grid_d[['ccname','消费金额']].groupby(by='ccname').sum()
re4=consume_num_grid_d[['ccname','消费次数']].groupby(by='ccname').sum()
re5=pd.merge(re3,re4,left_index=True,right_index=True)
re5=re5.reset_index()
re5['桌均']=re5['消费金额']/re5['消费次数']
# print(re5.head())

# 计算所有会员的桌均，用来衡量收银员操作可能出现的问题，如果单笔消费金额低于桌均的五分之一就认为该笔操作存在问题，因为很少有超过5个人一起过来消费的
total_consume=re5['消费金额'].sum()
total_consume_times=re5['消费次数'].sum()
# print(total_consume,total_consume_times)
consume_avg=total_consume/total_consume_times
consume_avg_5=consume_avg/5
# print(consume_avg_5)
# 这儿的16和下面的重复了，所以改成161
bar_h(161,re5['ccname'],re5['桌均'],'各等级会员桌均')




# 4.各分店的营业额与桌均
consume_month_sid='''select  sname '分店名',sum(tctotalfee/100) '消费金额',
count(1) '消费次数',count(distinct(uid)) '消费人数',
sum(tctotalfee/100)/count(1) as '消费桌均'
from dprpt_welife_trade_consume_detail 
where bid=%i
and ftime>=%s
and ftime<%s
and tctype=2
and length(sname)>0
group by sname''' %(p.bid,p.ftime_s,p.ftime_e)
print('4计算分店的营业额和桌均')
consume_month_sid_d=dwsql(consume_month_sid)
# print(consume_month_sid_d.head())
# 如果不int的话求不出平均值
consume_month_sid_d['消费金额']=consume_month_sid_d['消费金额'].apply(lambda x:int(x))
consume_month_sid_d['消费桌均']=consume_month_sid_d['消费桌均'].apply(lambda x:int(x))
consume_month_sid_d['消费桌均2']=consume_month_sid_d['消费桌均'].apply(lambda x:-int(x))
consume_month_sid_d_avg=consume_month_sid_d.mean().apply(lambda x:int(x))
# print(consume_month_sid_d_avg['消费次数'])
# 因为消费金额和桌均之间差了好几个量级，所以只能人为的传递一个量级进去，这样才能画出量小的柱子，而桌均是消费金额除以消费次数得来的，所以传递
# 消费次数的均值即可

# 现在根据门店的多少来决定画几张图，如果30家门店一下，画一张，30-60家画两张，60-90家画三张，90家以上画四张
if len(consume_month_sid_d)>=30 and len(consume_month_sid_d) < 60:
    a=int(len(consume_month_sid_d)/2)
    consume_month_sid_d_30=consume_month_sid_d.iloc[0:int('%s' %a) ,:]
    consume_month_sid_d_61=consume_month_sid_d.iloc[int('%s' %(a+1)):int('%s' %(2*a)),:]
    xuanf2(45,consume_month_sid_d_30['分店名'],consume_month_sid_d_30['消费金额'],consume_month_sid_d_30['消费桌均'],consume_month_sid_d_avg['消费次数'],'分店消费金额和桌均对比1','消费金额','桌均')
    xuanf2(46,consume_month_sid_d_61['分店名'],consume_month_sid_d_61['消费金额'],consume_month_sid_d_61['消费桌均'],consume_month_sid_d_avg['消费次数'],'分店消费金额和桌均对比2','消费金额','桌均')
elif len(consume_month_sid_d)>=60 and len(consume_month_sid_d) < 90:
    a=int(len(consume_month_sid_d)/3)
    consume_month_sid_d_30=consume_month_sid_d.iloc[0:int('%s' %a) ,:]
    consume_month_sid_d_61=consume_month_sid_d.iloc[int('%s' %(a+1)):int('%s' %(2*a)),:]
    consume_month_sid_d_91=consume_month_sid_d.iloc[int('%s' %(2*a)):int('%s'%(3*a)) ,:]
    xuanf2(45,consume_month_sid_d_30['分店名'],consume_month_sid_d_30['消费金额'],consume_month_sid_d_30['消费桌均'],consume_month_sid_d_avg['消费次数'],'分店消费金额和桌均对比1','消费金额','桌均')
    xuanf2(46,consume_month_sid_d_61['分店名'],consume_month_sid_d_61['消费金额'],consume_month_sid_d_61['消费桌均'],consume_month_sid_d_avg['消费次数'],'分店消费金额和桌均对比2','消费金额','桌均')
    xuanf2(47,consume_month_sid_d_91['分店名'],consume_month_sid_d_91['消费金额'],consume_month_sid_d_91['消费桌均'],consume_month_sid_d_avg['消费次数'],'分店消费金额和桌均对比3','消费金额','桌均')
elif len(consume_month_sid_d)>=90:
    a=int(len(consume_month_sid_d)/4)
    consume_month_sid_d_30=consume_month_sid_d.iloc[0:int('%s' %a) ,:]
    consume_month_sid_d_61=consume_month_sid_d.iloc[int('%s' %(a+1)):int('%s' %(2*a)),:]
    consume_month_sid_d_91=consume_month_sid_d.iloc[int('%s' %(2*a)):int('%s'%(3*a)) ,:]
    consume_month_sid_d_121=consume_month_sid_d.iloc[int('%s'%(3*a)) :,:]
    xuanf2(45,consume_month_sid_d_30['分店名'],consume_month_sid_d_30['消费金额'],consume_month_sid_d_30['消费桌均'],consume_month_sid_d_avg['消费次数'],'分店消费金额和桌均对比1','消费金额','桌均')
    xuanf2(46,consume_month_sid_d_61['分店名'],consume_month_sid_d_61['消费金额'],consume_month_sid_d_61['消费桌均'],consume_month_sid_d_avg['消费次数'],'分店消费金额和桌均对比2','消费金额','桌均')
    xuanf2(47,consume_month_sid_d_91['分店名'],consume_month_sid_d_91['消费金额'],consume_month_sid_d_91['消费桌均'],consume_month_sid_d_avg['消费次数'],'分店消费金额和桌均对比3','消费金额','桌均')
    xuanf2(48,consume_month_sid_d_121['分店名'],consume_month_sid_d_121['消费金额'],consume_month_sid_d_121['消费桌均'],consume_month_sid_d_avg['消费次数'],'分店消费金额和桌均对比4','消费金额','桌均')
else:
    xuanf2(17,consume_month_sid_d['分店名'],consume_month_sid_d['消费金额'],consume_month_sid_d['消费桌均'],consume_month_sid_d_avg['消费次数'],'分店消费金额和桌均对比','消费金额','桌均')




# 消费密度部分(备注：在跑其他的数据，这里还没有验证）
print('    4.1各等级的消费均次')
# print(consume_num_grid_d1.head())
consume_num_grid_d2=pd.merge(consume_num_grid_d1,ccname_d,on='grid')
# print(consume_num_grid_d2)
consume_num_grid_d2=pd.pivot_table(consume_num_grid_d2,index='ccname',values=['消费次数','消费人数'],aggfunc=sum)
consume_num_grid_d2=consume_num_grid_d2.reset_index()
consume_num_grid_d2['消费均次']=consume_num_grid_d2['消费次数']/consume_num_grid_d2['消费人数']

# print(consume_num_grid_d2)
bar_h2(18,consume_num_grid_d2['ccname'],consume_num_grid_d2['消费均次'],'各等级消费均次(月)')
plt.ylabel('消费均次')




# 5.消费转化率
consume_rate='''select trade_num '消费次数',count(uid) '消费人数'                                                                                                    
from (select uid,count(1) trade_num
from dprpt_welife_trade_consume_detail 
where ftime>=%s
and ftime<=%s
and tctype=2 and bid=%i
group by uid) a
group by trade_num
order by trade_num desc ''' %(p.ftime_s,p.ftime_e,p.bid)
print('5消费转化率')
consume_rate_d=dwsql(consume_rate)
consume_rate_d['consume_pop_num']=consume_rate_d['消费人数'].cumsum()
consume_rate_d=consume_rate_d.sort_values(by='消费次数')
consume_rate_d['conversion_rate']=consume_rate_d['consume_pop_num'].rolling(2).apply(lambda x:x.min()/x.max())
# consume_rate_d['conversion_rate']=consume_rate_d['conversion_rate'].apply(lambda x:float('%.2f' %x))
# 将“次”加在消费次数上
consume_rate_d['消费次数_ci']=consume_rate_d['消费次数'].apply(lambda x:str(x))+'次'
consume_rate_d=consume_rate_d[consume_rate_d['消费次数']<=25]
xuanf(19,consume_rate_d['消费次数'],consume_rate_d['消费次数_ci'],consume_rate_d['consume_pop_num'],consume_rate_d['conversion_rate'],'消费转化率','消费人数','转化率')


# 6消费近度
consume_week='''select date_format(tclcreated,'%%w') 'w',
count(1) '消费次数',
round(sum(tctotalfee/100)/count(1),0) '桌均消费金额'
from dprpt_welife_trade_consume_detail
where ftime>=%s and ftime<%s and bid=%i
and tctype=2 
group by date_format(tclcreated,'%%w') ''' %(p.ftime_s,p.ftime_e,p.bid)
print('6周消费次数和桌均')
consume_week_d=dwsql(consume_week)
consume_week_d.ix[0,0]=7
consume_week_d['w']=consume_week_d['w'].apply(lambda x:int(x))
consume_week_d=consume_week_d.sort_values(by='w')
consume_week_d['星期']=['周一','周二','周三','周四','周五','周六','周天']
consume_week_d['周一']=consume_week_d['消费次数'].ix[1,1]
consume_week_d['次数权重(除以周一次数)']=consume_week_d['消费次数']/consume_week_d['周一']
xuanf(20,consume_week_d['w'],consume_week_d['星期'],consume_week_d['桌均消费金额'],consume_week_d['次数权重(除以周一次数)'],
      '一周内每天消费次数和桌均对比','桌均','次数权重(除以周一次数)')
      


# 7.储过值会员和没有储值会员的消费周期和会员的流逝状态

# 7.1消费周期
# 储值过的会员的第二次消费时间,之所以rank<3,这样可以一次性的取出第一次的消费和第二次的消费
charge_vip='''  SELECT
    uid,
    fee,
    ftime_2,
    rank,
    ac_fee,
    charge_type
FROM
    (
        SELECT
            uid,
            fee,
            ftime_2,
            charge_type,
            @x :=
        IF (@user_uid = uid ,@x + 1, 1) AS rank,
        @y :=
    IF (@user_uid = uid ,@y + fee, fee) AS ac_fee,
    @user_uid := uid AS dummy
FROM
    (
        SELECT
            c.uid,
            date_format(tccreated, '%%Y%%m%%d') AS ftime_2,
            tctotalfee / 100 AS fee,
            CASE
        WHEN tcStoredPay > 0 THEN
            'charge_vip'
        ELSE
            'non_charge_vip'
        END AS charge_type
        FROM
            welife_trade_consumes c
        WHERE
            bid = %s
        AND tcstatus = 2
        AND tctype IN (2, 8)
    ) t2,
    (
        SELECT
            @x := 0 ,@y := 0 ,@user_uid := NULL
    ) t1
ORDER BY
    uid,
    ftime_2
    ) result
WHERE
    rank < 3
AND charge_type = 'charge_vip'  ''' %(p.bid)
print('7储值过消费周期')
charge_vip_d=wesql(charge_vip)
if  charge_vip_d.empty:
    charge_vip_d=pd.DataFrame({'rank':[1,2],'ftime_2':[20170101,20180101],'ac_fee':[0,0],'charge_type':[0,0],'fee':[0,0],'uid':[0,0]},index=[0,1])
# 取出第一次消费
charge_vip_d_1=charge_vip_d[charge_vip_d['rank']==1]
# 取出第二次消费
charge_vip_d_2=charge_vip_d[charge_vip_d['rank']==2]
charge_re1=pd.merge(charge_vip_d_1,charge_vip_d_2,on='uid')

# 从原始的数据框里面选出只想要的列
charge_re1=charge_re1[['uid','ftime_2_x','ftime_2_y']]
# 转化成时间，然后相减
charge_re1['ftime_1']=charge_re1['ftime_2_x'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
charge_re1['ftime_2']=charge_re1['ftime_2_y'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
charge_re1['interval']=charge_re1['ftime_2']-charge_re1['ftime_1']

# 求出每一个用户的两次间隔天数
charge_re1['days']=charge_re1['interval'].apply(lambda x:x.days)

# 之所以要加if是因为有些商户确实没有开通储值的功能，这样画不出来的储值会员的消费周期，所以手动的修改了第一次和第二次消费的天数，以假装
# 可以算出消费周期,注意如果画出来的图里面消费周期是1的话，就是有问题的说明没有储值会员，需要被删除
if any(charge_re1['days'])<1:
    charge_re1['days']=1  
# 应该来说间隔天数为0 ，是不对的，所以最好去掉，很有可能就是券的核销和消费算作同一次了
charge_re1=charge_re1[charge_re1['days']>0]


# print(charge_re1)
charge_vip_mean=charge_re1['days'].mean()
# print('charge_vip_mean',charge_re1['days'].mean())
# print(charge_re1.tail(10))
charge_re2=pd.pivot_table(charge_re1,index='days',values='uid',aggfunc=len)

charge_re2=charge_re2.reset_index()
# 添加两列。一列是累计的人数一列是总人数,累计的数量是为了画出那条红色的累计曲线
# print(charge_re2.head())
if not charge_re2.empty:
    
    charge_re2['pop_cum']=charge_re2['uid'].cumsum()
    charge_re2['totalsum']=charge_re2['uid'].sum()
    # 求出累计占比
    charge_re2['rate']=charge_re2['pop_cum']/charge_re2['totalsum']
    
    
    # xuanf1没有添加数据标签，所以不用xuanf
    # xuanf1(21,charge_re2['days'],charge_re2['uid'],charge_re2['rate'],'储值过会员消费周期','人数','累计占比',charge_vip_mean)
    # 要画出唤醒的标签，现在不会直接用xuanf1之后，在对原来的图片进行修改，于是重新写一遍
    
    # =========================================以下就是画出消费周期，并且标注唤醒点============================================================
    #charge_vip_mean如果是空的话，先赋值为0
    cycle=int(charge_vip_mean)

    

    fig=plt.figure(21,figsize=(10,6),dpi=200)
    ax1=fig.add_subplot(111)
    bar_p=ax1.bar(charge_re2['days'],charge_re2['uid'])
    plt.annotate('消费周期:%s天' %int(round(cycle,0)),xy=(charge_re2['days'].mean(),charge_re2['uid'].mean()+100),fontsize=20,color='r')
    ax2=ax1.twinx()
    line_p,=ax2.plot(charge_re2['days'],charge_re2['rate'],'r')


    # 1.在消费周期处唤醒
    # 思路是先让列表里面的值小于等于消费周期，然后取出新列表的最大值就是最接近消费周期的值，再取出该值对应的rate
    cycle_1=charge_re2[charge_re2['days']<=cycle]['rate']
    cycle_dot2=cycle_1.nlargest(1).values[0]
    cycle_dot2_bai='%1.f%%' %((1-cycle_dot2)*100)
    # 在曲线上标出一个散点
    ax2.scatter(cycle,cycle_dot2,s=25,color='b')    
    ax2.hlines(cycle_dot2,xmin=cycle,xmax=300,linestyles='dashed')
    ax2.vlines(cycle,ymin=0,ymax=cycle_dot2,linestyles='dashed')
    # xytext和textcoords是对点的平移设置
    
    ax2.annotate('消费周期%s天，此时%s客人需要唤醒' %(cycle,cycle_dot2_bai),xy=(cycle,cycle_dot2),xytext=(100,7),textcoords='offset points')

    



# 以前画消费周期的时候还画出来20%和80%的唤醒点，后来取消
# # 2.20%处唤醒
# a1=0.2
# b1=charge_re2[charge_re2['rate']<=a1]
# b1_rate=b1['rate'].nlargest(1).values[0]
# b1_rate_bai='%1.f%%' %((1-b1_rate)*100)
# b1_days=b1['days'].nlargest(1).values[0]
# ax2.scatter(b1_days,b1_rate,s=25,color='b')
# ax2.hlines(b1_rate,xmin=b1_days,xmax=300,linestyles='dashed')
# ax2.vlines(b1_days,ymin=0,ymax=b1_rate,linestyles='dashed')
# ax2.annotate('%s天唤醒%s客人' %(b1_days,b1_rate_bai),xy=(b1_days,b1_rate),xytext=(100,7),textcoords='offset points')
# 
# # 3.80%处唤醒
# a11=0.8
# b11=charge_re2[charge_re2['rate']<=a11]
# b11_rate=b11['rate'].nlargest(1).values[0]
# b11_rate_bai='%1.f%%' %((1-b11_rate)*100)
# b11_days=b11['days'].nlargest(1).values[0]
# ax2.scatter(b11_days,b11_rate,s=25,color='b')
# ax2.hlines(b11_rate,xmin=b11_days,xmax=300,linestyles='dashed')
# ax2.vlines(b11_days,ymin=0,ymax=b11_rate,linestyles='dashed')
# ax2.annotate('%s天唤醒%s客人' %(b11_days,b11_rate_bai),xy=(b11_days,b11_rate),xytext=(100,7),textcoords='offset points')




    plt.title('储值过会员消费周期')
    plt.legend([bar_p,line_p],['%s' %'人数','%s' %'累计占比'],loc=3,bbox_to_anchor=[0,1],fontsize='small')
    plt.savefig('21储值过会员消费周期')
else:
    fig=plt.figure(21,figsize=(10,6),dpi=200)
    plt.bar(0,0)
    plt.savefig('21储值过会员消费周期')
# =========================================以上就是画出消费周期，并且标注唤醒点============================================================



# 7.2根据求出来的mean来划分会员的状态
charge_vip_churn_rate='''select uid,max(ftime) as max_time,charge_type
from (
select c.uid ,date_format(tccreated,'%%Y%%m%%d')  as ftime,tctotalfee/100 as fee,
case when tcStoredPay>0 then 'charge_vip'
else  'non_charge_vip'
end as charge_type
from 
welife_trade_consumes c
where  bid=%i and tcstatus=2 and tctype in (2,8)  ) a
where charge_type='charge_vip'
group by uid''' %(p.bid)
print('    7.1储值过各等级流失率')
charge_vip_churn_rate_d=wesql(charge_vip_churn_rate)
if charge_vip_churn_rate_d.empty:
    charge_vip_churn_rate_d=pd.DataFrame({'max_time':[20170101],'uid':0,'charge_type':[0]},index=[0])
charge_vip_churn_rate_d['today']=datetime.now().strftime("%Y%m%d")
charge_vip_churn_rate_d['max_time']=charge_vip_churn_rate_d['max_time'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
charge_vip_churn_rate_d['today']=charge_vip_churn_rate_d['today'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
charge_vip_churn_rate_d['interval']=charge_vip_churn_rate_d['today']-charge_vip_churn_rate_d['max_time']
charge_vip_churn_rate_d['days']=charge_vip_churn_rate_d['interval'].apply(lambda x:x.days)
# 将今天的时间和会员的最后一天相减之后，再用np.where判定出会员的状态
charge_vip_churn_rate_d['status']=np.where(charge_vip_churn_rate_d['days']>3*charge_vip_mean,'沉睡会员' ,
                                           np.where((charge_vip_churn_rate_d['days']>2*charge_vip_mean)&(charge_vip_churn_rate_d['days']<=3*charge_vip_mean),'半睡会员',
                                                                                                               np.where((charge_vip_churn_rate_d['days']>charge_vip_mean)&(charge_vip_churn_rate_d['days']<=2*charge_vip_mean),'瞌睡会员','活跃会员')))
 
charge_vip_churn_rate_d_re3=pd.pivot_table(charge_vip_churn_rate_d,index='status',values='uid',aggfunc=len)
charge_vip_churn_rate_d_re3=charge_vip_churn_rate_d_re3.reset_index()
charge_vip_churn_rate_d_re3['total']=charge_vip_churn_rate_d_re3['uid'].sum()
charge_vip_churn_rate_d_re3['rate']=charge_vip_churn_rate_d_re3['uid']/charge_vip_churn_rate_d_re3['total']
# w=pd.ExcelWriter('储值会员流失占比.xlsx')
# charge_vip_churn_rate_d_re3.to_excel(w,'流失')
# w.save()
# print(charge_vip_churn_rate_d_re3.head())
bar_h3(23,charge_vip_churn_rate_d_re3.index,charge_vip_churn_rate_d_re3['status'],charge_vip_churn_rate_d_re3['rate'],'储值会员不同程度流失数量占比')


# 以上是各等级的流逝数量，还想要画出各分店流失会员数量
# 7.3各分店的流逝会员数量,依据sid,和uid来group,这样即使存在跨店消费的也会算在某个店的流逝上
charge_vip_churn_rate_sid='''select sname,uid,charge_type,max(ftime) as max_time
from (
select c.uid ,sname,date_format(tccreated,'%%Y%%m%%d')  as ftime,tctotalfee/100 as fee,
case when tcStoredPay>0 then 'charge_vip'
else  'non_charge_vip'
end as charge_type
from 
welife_trade_consumes c inner join welife_shops shop on c.bid=shop.bid and  c.sid=shop.sid
where  c.bid=%i and tcstatus=2 and tctype in (2,8)  ) a
where charge_type='charge_vip'
group by sname,charge_type,uid''' %(p.bid)
print('    7.2储值过分店流失数量')
charge_vip_churn_rate_sid_d=wesql(charge_vip_churn_rate_sid)
if charge_vip_churn_rate_sid_d.empty:
    charge_vip_churn_rate_sid_d=pd.DataFrame({'sname':0,'uid':0,'charge_type':0,'max_time':20170101},index=[0])
# print(charge_vip_churn_rate_sid_d.head())
if not charge_vip_mean>0:  #如果charge_vip_mean是空值的话，就暂时赋值为0
    charge_vip_mean=0

to_days(charge_vip_churn_rate_sid_d,charge_vip_churn_rate_sid_d['max_time'],charge_vip_mean)
# print(charge_vip_churn_rate_sid_d.tail())
charge_vip_churn_rate_sid_d=pd.pivot_table(charge_vip_churn_rate_sid_d,index=['sname','status'],values='uid',aggfunc=len)
charge_vip_churn_rate_sid_d=charge_vip_churn_rate_sid_d.reset_index()
# print(charge_vip_churn_rate_sid_d.head())
charge_vip_churn_rate_sid_d_liushi=charge_vip_churn_rate_sid_d[charge_vip_churn_rate_sid_d['status']=='沉睡会员']
charge_vip_churn_rate_sid_d_liushi=charge_vip_churn_rate_sid_d_liushi.sort_values(by='uid',ascending=False)
# print(charge_vip_churn_rate_sid_d_liushi)
charge_vip_churn_rate_sid_d_liushi=charge_vip_churn_rate_sid_d_liushi.sort_values(by='uid',ascending=False)
charge_vip_churn_rate_sid_d_liushi=charge_vip_churn_rate_sid_d_liushi.nlargest(20, 'uid')
w_liushi=pd.ExcelWriter('charge_vip_churn_rate_sid_d_liushi.xlsx')
charge_vip_churn_rate_sid_d_liushi.to_excel(w_liushi,'charge')
if len(charge_vip_churn_rate_sid_d_liushi)<20:
    bar_h(25,charge_vip_churn_rate_sid_d_liushi['sname'],charge_vip_churn_rate_sid_d_liushi['uid'],'分店储值过会员的流失数量')
else:
    bar_h(25,charge_vip_churn_rate_sid_d_liushi['sname'],charge_vip_churn_rate_sid_d_liushi['uid'],'分店储值过会员的流失数量_前20家门店')
# else:
#     w_liushi=pd.ExcelWriter('charge_vip_churn_rate_sid_d_liushi.xlsx')
#     charge_vip_churn_rate_sid_d_liushi.to_excel(w_liushi,'charge')
#     fig=plt.figure(25)
#     plt.bar(0,0)
#     plt.savefig('25分店储值过会员的流失数量_前20家门店')





# 没有储值过的会员的消费周期（没有储值过的情况和储值过的会员的取数据方式几乎一样，所以不在描叙
non_charge_vip='''  SELECT
    uid,
    fee,
    ftime_2,
    rank,
    ac_fee,
    charge_type
FROM
    (
        SELECT
            uid,
            fee,
            ftime_2,
            charge_type,
            @x :=
        IF (@user_uid = uid ,@x + 1, 1) AS rank,
        @y :=
    IF (@user_uid = uid ,@y + fee, fee) AS ac_fee,
    @user_uid := uid AS dummy
FROM
    (
        SELECT
            c.uid,
            date_format(tccreated, '%%Y%%m%%d') AS ftime_2,
            tctotalfee / 100 AS fee,
            CASE
        WHEN tcStoredPay > 0 THEN
            'charge_vip'
        ELSE
            'non_charge_vip'
        END AS charge_type
        FROM
            welife_trade_consumes c
        WHERE
            bid = %s
        AND tcstatus = 2
        AND tctype IN (2, 8)
    ) t2,
    (
        SELECT
            @x := 0 ,@y := 0 ,@user_uid := NULL
    ) t1
ORDER BY
    uid,
    ftime_2
    ) result
WHERE
    rank < 3
AND charge_type = 'non_charge_vip'  ''' %(p.bid)
print('    7.3未储值过的消费周期')
non_charge_vip_d=wesql(non_charge_vip)


# 有时候non_charge_vip_d是空的，所以人为的制造了一个non_charge_vip_d的数据框
if non_charge_vip_d.empty:
    non_charge_vip_d=pd.DataFrame({'ac_fee':[0,0],'charge_type':['non_charge_vip','non_charge_vip'],'fee':[0,0],'ftime_2':[20170101,20170201],'rank':[1,2],'uid':[000,000]},index=[0,1])   



non_charge_vip_d_1=non_charge_vip_d[non_charge_vip_d['rank']==1]
non_charge_vip_d_2=non_charge_vip_d[non_charge_vip_d['rank']==2]
non_charge_re2=pd.merge(non_charge_vip_d_1,non_charge_vip_d_2,on='uid')
non_charge_re2=non_charge_re2[['uid','ftime_2_x','ftime_2_y']]
non_charge_re2['ftime_1']=non_charge_re2['ftime_2_x'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
non_charge_re2['ftime_2']=non_charge_re2['ftime_2_y'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
non_charge_re2['interval']=non_charge_re2['ftime_2']-non_charge_re2['ftime_1']
non_charge_re2['days']=non_charge_re2['interval'].apply(lambda x:x.days)
# 这个地方出现了days=0的情况，而且是极大值，所以去掉
non_charge_re2=non_charge_re2[non_charge_re2['days']>0]

# print(non_charge_re2['days'].mean())
non_charge_vip_mean=non_charge_re2['days'].mean()
# print('non_charge_vip_mean,',non_charge_vip_mean)
non_charge_re2_re2=pd.pivot_table(non_charge_re2,index='days',values='uid',aggfunc=len)
# print(non_charge_re2_re2)
non_charge_re2_re2=non_charge_re2_re2.reset_index()

# print(non_charge_re2_re2.head())
if non_charge_re2_re2.empty:
    non_charge_re2_re2=pd.DataFrame({'uid':0,'days':0},index=[0])
    
non_charge_re2_re2['pop_cum']=non_charge_re2_re2['uid'].cumsum()
non_charge_re2_re2['totalsum']=non_charge_re2_re2['uid'].sum()
non_charge_re2_re2['rate']=non_charge_re2_re2['pop_cum']/non_charge_re2_re2['totalsum']
# xuanf1(22,non_charge_re2_re2['days'],non_charge_re2_re2['uid'],non_charge_re2_re2['rate'],'非储值会员的消费周期','人数','累计占比',non_charge_vip_mean)


# =========================================以下就是画出消费周期，并且标注唤醒点============================================================
if  non_charge_vip_mean>0:
    cycle_non=int(non_charge_vip_mean)
else:
    cycle_non=0

fig=plt.figure(22,figsize=(10,6),dpi=200)
ax1=fig.add_subplot(111)
bar_p=ax1.bar(non_charge_re2_re2['days'],non_charge_re2_re2['uid'])
plt.annotate('消费周期:%s天' %int(round(cycle_non,0)),xy=(non_charge_re2_re2['days'].mean(),non_charge_re2_re2['uid'].mean()+100),fontsize=20,color='r')
ax2=ax1.twinx()
line_p,=ax2.plot(non_charge_re2_re2['days'],non_charge_re2_re2['rate'],'r')


# 1.在消费周期处唤醒

cycle_1=non_charge_re2_re2[non_charge_re2_re2['days']<=cycle_non]['rate']
# print(cycle_1)
if cycle_1.empty:
    cycle_dot2=0
else:
    cycle_1=cycle_1.fillna(0)
    cycle_dot2=cycle_1.nlargest(1).values[0]
cycle_dot2_bai='%1.f%%' %((1-cycle_dot2)*100)
ax2.scatter(cycle_non,cycle_dot2,s=25,color='b')    
ax2.hlines(cycle_dot2,xmin=cycle_non,xmax=300,linestyles='dashed')
ax2.vlines(cycle_non,ymin=0,ymax=cycle_dot2,linestyles='dashed')
ax2.annotate('消费周期%s天，此时%s客人需要唤醒'  %(cycle_non,cycle_dot2_bai),xy=(cycle_non,cycle_dot2),xytext=(100,7),textcoords='offset points')



# 原因和储值会员的消费额周期一样，请看上面的注释
# # 2.20%处唤醒
# a1=0.2
# b1=non_charge_re2_re2[non_charge_re2_re2['rate']<=a1]
# b1_rate=b1['rate'].nlargest(1).values[0]
# b1_rate_bai='%1.f%%' %((1-b1_rate)*100)
# b1_days=b1['days'].nlargest(1).values[0]
# ax2.scatter(b1_days,b1_rate,s=25,color='b')
# ax2.hlines(b1_rate,xmin=b1_days,xmax=300,linestyles='dashed')
# ax2.vlines(b1_days,ymin=0,ymax=b1_rate,linestyles='dashed')
# ax2.annotate('%s天唤醒%s客人' %(b1_days,b1_rate_bai),xy=(b1_days,b1_rate),xytext=(100,7),textcoords='offset points')
# 
# # 3.80%处唤醒
# a11=0.8
# b11=non_charge_re2_re2[non_charge_re2_re2['rate']<=a11]
# b11_rate=b11['rate'].nlargest(1).values[0]
# b11_rate_bai='%1.f%%' %((1-b11_rate)*100)
# b11_days=b11['days'].nlargest(1).values[0]
# ax2.scatter(b11_days,b11_rate,s=25,color='b')
# ax2.hlines(b11_rate,xmin=b11_days,xmax=300,linestyles='dashed')
# ax2.vlines(b11_days,ymin=0,ymax=b11_rate,linestyles='dashed')
# ax2.annotate('%s天唤醒%s客人' %(b11_days,b11_rate_bai),xy=(b11_days,b11_rate),xytext=(100,7),textcoords='offset points')


plt.title('非储值会员的消费周期')
plt.legend([bar_p,line_p],['%s' %'人数','%s' %'累计占比'],loc=3,bbox_to_anchor=[0,1],fontsize='small')
plt.savefig('22非储值会员的消费周期')

# =========================================以上就是画出消费周期，并且标注唤醒点==============

# 根据求出来的mean来划分会员的状态
non_charge_vip_mean_sql='''select uid,charge_type,max(ftime) as max_time
from (
select c.uid ,date_format(tccreated,'%%Y%%m%%d')  as ftime,tctotalfee/100 as fee,
case when tcStoredPay>0 then 'charge_vip'
else  'non_charge_vip'
end as charge_type
from 
(select uid,tccreated,tctotalfee,tcStoredPay
from welife_trade_consumes 
where bid=%i and tccreated>=%s and tccreated<%s and 
tcstatus=2 and tctype in (2,8)) c) a
where charge_type='non_charge_vip'
group by uid,charge_type''' %(p.bid,p.ftime_s,p.ftime_e)
print('    7.4未储值过流失率')
non_charge_vip_churn_rate_d=wesql(non_charge_vip_mean_sql)

    
if non_charge_vip_churn_rate_d.empty:
    non_charge_vip_churn_rate_d=pd.DataFrame({'uid':0,'max_time':'20170101','charge_type':0},index=[0,1])   

    
    
non_charge_vip_churn_rate_d['today']=datetime.now().strftime("%Y%m%d")
non_charge_vip_churn_rate_d['max_time']=non_charge_vip_churn_rate_d['max_time'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
non_charge_vip_churn_rate_d['today']=non_charge_vip_churn_rate_d['today'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
non_charge_vip_churn_rate_d['interval']=non_charge_vip_churn_rate_d['today']-non_charge_vip_churn_rate_d['max_time']
non_charge_vip_churn_rate_d['days']=non_charge_vip_churn_rate_d['interval'].apply(lambda x:x.days)
non_charge_vip_churn_rate_d['status']=np.where(non_charge_vip_churn_rate_d['days']>3*non_charge_vip_mean,'沉睡会员',
                                           np.where((non_charge_vip_churn_rate_d['days']>2*non_charge_vip_mean)&(non_charge_vip_churn_rate_d['days']<=3*non_charge_vip_mean),'瞌睡会员',
                                                                                                               np.where((non_charge_vip_churn_rate_d['days']>non_charge_vip_mean)&(non_charge_vip_churn_rate_d['days']<=2*non_charge_vip_mean),'半睡会员','活跃会员')))
 
non_charge_vip_churn_rate_d_re3=pd.pivot_table(non_charge_vip_churn_rate_d,index='status',values='uid',aggfunc=len)
non_charge_vip_churn_rate_d_re3=non_charge_vip_churn_rate_d_re3.reset_index()
non_charge_vip_churn_rate_d_re3['total']=non_charge_vip_churn_rate_d_re3['uid'].sum()
non_charge_vip_churn_rate_d_re3['rate']=non_charge_vip_churn_rate_d_re3['uid']/non_charge_vip_churn_rate_d_re3['total']

# print(non_charge_vip_churn_rate_d_re3.head())
bar_h3(24,non_charge_vip_churn_rate_d_re3.index,non_charge_vip_churn_rate_d_re3['status'],non_charge_vip_churn_rate_d_re3['rate'],'非储值会员不同程度流失数量占比')




# 分店非储值会员的流逝数量
non_charge_vip_churn_rate_sid='''select sname,uid,charge_type,max(ftime) as max_time
from (
select c.uid ,sname,date_format(tccreated,'%%Y%%m%%d')  as ftime,tctotalfee/100 as fee,
case when tcStoredPay>0 then 'charge_vip'
else  'non_charge_vip'
end as charge_type
from 

(select uid,tccreated,tctotalfee,sid,bid,tcStoredPay
from welife_trade_consumes 
where bid=%i and  tccreated>=%s and tccreated<%s and 
tcstatus=2 and tctype in (2,8)) c 
inner join welife_shops shop on c.bid=shop.bid and  c.sid=shop.sid) a
where charge_type='non_charge_vip'
group by sname,charge_type,uid''' %(p.bid,p.ftime_s,p.ftime_e)
print('    7.5未储值过会员分店的流失数量')
non_charge_vip_churn_rate_sid_d=wesql(non_charge_vip_churn_rate_sid)

if non_charge_vip_churn_rate_sid_d.empty:
    non_charge_vip_churn_rate_sid_d=pd.DataFrame({'uid':0,'max_time':'20170101','charge_type':0},index=[0,1])   


if not non_charge_vip_mean>0:
    non_charge_vip_mean=0
    
    
to_days(non_charge_vip_churn_rate_sid_d,non_charge_vip_churn_rate_sid_d['max_time'],non_charge_vip_mean)
print(charge_vip_churn_rate_sid_d.tail())
non_charge_vip_churn_rate_sid_d=pd.pivot_table(non_charge_vip_churn_rate_sid_d,index=['sname','status'],values='uid',aggfunc=len)
non_charge_vip_churn_rate_sid_d=non_charge_vip_churn_rate_sid_d.reset_index()

# 这儿报了一个奇怪的错误，所以加了这一句status的类型转换
non_charge_vip_churn_rate_sid_d['status']=non_charge_vip_churn_rate_sid_d['status'].apply(lambda x:str(x))



non_charge_vip_churn_rate_sid_d_liushi=non_charge_vip_churn_rate_sid_d[non_charge_vip_churn_rate_sid_d['status']=='沉睡会员']

if non_charge_vip_churn_rate_sid_d_liushi.empty:
    non_charge_vip_churn_rate_sid_d_liushi=pd.DataFrame({'uid':0,'sname':'需要删除'},index=[0])
    
non_charge_vip_churn_rate_sid_d_liushi=non_charge_vip_churn_rate_sid_d_liushi.sort_values(by='uid',ascending=False)
non_charge_vip_churn_rate_sid_d_liushi=non_charge_vip_churn_rate_sid_d_liushi.nlargest(20, 'uid')
non_charge_vip_churn_rate_sid_d_liushi.to_excel(w_liushi,'nocharge')
w_liushi.save()
if len(non_charge_vip_churn_rate_sid_d_liushi)<20:
    bar_h(26,non_charge_vip_churn_rate_sid_d_liushi['sname'],non_charge_vip_churn_rate_sid_d_liushi['uid'],'分店非储值会员的流失数量')
else:
    bar_h(26,non_charge_vip_churn_rate_sid_d_liushi['sname'],non_charge_vip_churn_rate_sid_d_liushi['uid'],'分店非储值会员的流失数量')
    


# 8.每月操作可能有问题订单数
action_error='''select date_format(tclcreated,'%%Y%%m') 'month',count(uid) 'total_num',
count(case when tcTotalFee/100<%s then uid end) 'error_num',
count(case when tcTotalFee/100<%s then uid end)/count(uid) 'error_rate'
from dprpt_welife_trade_consume_detail 
where bid=%i
and ftime>=%s
and ftime<=%s
and tctype=2
group by month'''  %(consume_avg_5,consume_avg_5,p.bid,p.ftime_s,p.ftime_e)
print('8.每月操作可能有问题订单')
action_error_d=dwsql(action_error)
fig=plt.figure(43,figsize=(10,6))
plt.plot(action_error_d['month'],action_error_d['error_rate'],'-o')

autolabel2(action_error_d['month'],action_error_d['error_rate'],12)
plt.xlabel('月份')
plt.ylabel('可能有问题操作占比')
plt.title('每月操作可能有问题占比')
plt.savefig('43每月操作可能有问题占比')



# 8.1分店操作可能有问题占比
action_error_sname='''select sname ,count(uid) 'total_num',
count(case when tcTotalFee/100<%s then uid end) 'error_num',
count(case when tcTotalFee/100<%s then uid end)/count(uid) 'error_rate'
from dprpt_welife_trade_consume_detail 
where bid=%i
and ftime>=%s
and ftime<=%s
and tctype=2
and length(sname)>0
group by sname'''   %(consume_avg_5,consume_avg_5,p.bid,p.ftime_s,p.ftime_e)
print('8.1分店可能有问题订单数')
action_error_sname_d=dwsql(action_error_sname)
# 取出占比最高的5家店面
action_error_sname_d_dayu=action_error_sname_d[action_error_sname_d['error_num']>0]
action_error_sname_d_5_sname=action_error_sname_d_dayu.nlargest(5, 'error_num')
# print(action_error_sname_d_5_sname)
bar_h2(44,action_error_sname_d_5_sname['sname'],action_error_sname_d_5_sname['error_rate'],'操作可能有问题占比较高门店')

w=pd.ExcelWriter('%s消费数据.xlsx' %p.sname)

consume_money_d.to_excel(w,'每月会员整体营业额')
re1.to_excel(w,'首次消费和再次消费')
consume_num_grid_d_pivot_table.to_excel(w,'各等级营业额')
re5.to_excel(w,'各等级桌均')
del consume_month_sid_d['消费桌均2']
consume_month_sid_d.to_excel(w,'各分店的营业额与桌均')
# 这个文件在to_pptx里面要用到，来判断门店数量的多少
w21=pd.ExcelWriter('各分店的营业额与桌均.xlsx')
consume_month_sid_d.to_excel(w21,'data')
w21.save()
consume_num_grid_d2.to_excel(w,'各等级消费均次(月)')
consume_rate_d=consume_rate_d.rename(columns={'consume_pop_num':'累计消费人数','conversion_rate':'转化率'})
consume_rate_d[['累计消费人数','转化率']].to_excel(w,'消费转化率')
consume_week_d.to_excel(w,'周内各天消费')

charge_vip_churn_rate_d_re3=charge_vip_churn_rate_d_re3.rename(columns={'status':'状态','uid':'人数','rate':'占比'})
charge_vip_churn_rate_d_re3[['状态','人数','占比']].to_excel(w,'储过值会员流失数量')
charge_vip_churn_rate_sid_d_liushi=charge_vip_churn_rate_sid_d_liushi.rename(columns={'sname':'门店','status':'状态','uid':'人数'})
charge_vip_churn_rate_sid_d_liushi.to_excel(w,'储过值分店流失数量')
non_charge_vip_churn_rate_d_re3=non_charge_vip_churn_rate_d_re3.rename(columns={'status':'状态','uid':'人数','rate':'占比'})
non_charge_vip_churn_rate_d_re3[['状态','人数','占比']].to_excel(w,'未储值会员流失数量')

non_charge_vip_churn_rate_sid_d_liushi=non_charge_vip_churn_rate_sid_d_liushi.rename(columns={'sname':'门店','status':'状态','uid':'人数'})
non_charge_vip_churn_rate_sid_d_liushi.to_excel(w,'未储值分店流失数量')
action_error_d.to_excel(w,'每月操作可能有问题订单')
action_error_sname_d_5_sname.to_excel(w,'分店可能有问题订单数')
w.save()

# close()



