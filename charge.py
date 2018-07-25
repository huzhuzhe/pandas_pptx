#-*- coding:utf-8 -*-
#"2018年1月3日"
from connect.connect import dwsql,wesql,pd,close
import matplotlib.pyplot as plt 
import datetime
import numpy as np
from  datetime import datetime
from pandas_pptx import public as p
from operator import itemgetter
from pandas_pptx.method import double_line2

print('=========================')
print('储值')
print('=========================')


plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号

# 获取分店名称
sname='''select sid,sname from welife_shops where bid=%i''' %p.bid
sname_d=wesql(sname)
sname_d['sid']=sname_d['sid'].apply(lambda x:str(x))


# 获取会员的等级
ccname='''select ccid,ccname as grid from welife_card_categories where bid=%i'''%p.bid
ccname_d=wesql(ccname)

# 1.储值金额消耗
charge_consume='''select date_format(ftime,'%%Y%%m') '月份',
sum(case when tctype in (2,8) then tclprinciple/100 end) - ifnull(sum(case when tctype=3 then tclprinciple/100 end),0) '储值实收消耗'
from dprpt_welife_trade_consume_detail
where bid=%i
and ftime>=%s
and ftime<%s
group by date_format(ftime,'%%Y%%m')'''  %(p.bid,p.ftime_s,p.ftime_e)
# 计算每月的储值消耗
print('1储值消耗')
charge_consume_d=dwsql(charge_consume)
charge_consume_d.fillna(0,inplace=True)
# print(charge_consume_d)
# 在名称里面加1其实是新增加了一列，因为千分位之后是str，求储值沉淀的时候不能相减，所以还是保留了原来的列
charge_consume_d['储值实收消耗1']=charge_consume_d['储值实收消耗'].apply(lambda x:"{:,}".format(int(x)))

# 2.储值金额实收
charge_tcsale='''select date_format(c.tccreated,'%%Y%%m') '月份',sum(c.tcsale/100) '储值金额实收'
from welife_trade_charges c 
where c.bid=%i
and c.tccreated >= %s 
and  c.tccreated < %s 
and tcChargeType <> 19
and c.tcStatus=1 and c.tctype=1
group by date_format(c.tccreated,'%%Y%%m')''' %(p.bid,p.ftime_s,p.ftime_e)
# 每个月的储值实收
print('2储值金额实收')
charge_tcsale_d=wesql(charge_tcsale)
if charge_tcsale_d.empty:
    charge_tcsale_d=charge_consume_d.copy()
    charge_tcsale_d.rename(columns={'储值实收消耗1':'储值金额实收1','储值实收消耗':'储值金额实收'},inplace=True)
#     print(charge_tcsale_d)
else:
    charge_tcsale_d['储值金额实收1']=charge_tcsale_d['储值金额实收'].apply(lambda x:"{:,}".format(int(x)))



# 81到86是后加的，如果有问题可以注释，然后跑原来的
charge_saving_and_consume=pd.merge(charge_tcsale_d,charge_consume_d,on='月份',how='left').fillna(0)
# print(charge_saving_and_consume)
charge_consume_list=['储值金额实收','储值实收消耗']
double_line2(1, charge_saving_and_consume['月份'], charge_saving_and_consume, '月份', '金额(单位：元)',
              charge_consume_list, '每月的储值实收和消耗')

# 3.计算每月的储值沉淀
print('3储值沉淀')
charge_saving=pd.merge(charge_tcsale_d,charge_consume_d,on=['月份'])


charge_saving['储值沉淀']=charge_saving['储值金额实收']-charge_saving['储值实收消耗']
charge_saving['储值沉淀']=charge_saving['储值沉淀'].apply(lambda x:int(x))
charge_saving['累计储值沉淀']=charge_saving['储值沉淀'].cumsum()
# w=pd.ExcelWriter('将太无二每月的储值沉淀.xlsx')
# charge_saving.to_excel(w,'data')
# w.save()
# close()
# print(charge_saving)

fig=plt.figure(2,figsize=(10,6))
my_index=np.arange(len(charge_saving))
plt.bar(my_index,charge_saving['储值沉淀'])
plt.plot(my_index,charge_saving['累计储值沉淀'],'r-o')


for a,b in zip(my_index,charge_saving['累计储值沉淀']):
    if a%2==0:
        plt.text(a,b,'{:,}'.format(b),ha='center',va='baseline',fontsize=13)
    
    
    
for a,b in zip(my_index,charge_saving['储值沉淀']):
        plt.text(a,b,'{:,}'.format(b),ha='center',va='baseline',fontsize=13)
    
    
    
plt.title('每月的储值沉淀')
plt.xlabel('月份')
plt.xticks(my_index,charge_saving['月份'],fontsize=12,rotation=30)
plt.legend(['累计储值沉淀','当月储值沉淀'])
plt.ylabel("金额（单位：元）")
plt.savefig('6每月的储值沉淀',dpi=200)



# 4.分店每月的储值金额
charge='''select sid,date_format(tcCreated,'%%Y%%m') as 'month',
sum(tcsale/100) as 'charge_mount',count(distinct(uid)) as 'charge_num'
from welife_trade_charges where bid=%i
and tcCreated >= %s
and tcCreated < %s
and tcType=1 and tcStatus=1 and tcChargeType <> 19
group by sid,month ''' %(p.bid,p.ftime_s,p.ftime_e)
print('4计算门店的所有储值')
charge_d=wesql(charge)

if not charge_d.empty:
    charge_d['charge_mount']=charge_d['charge_mount'].apply(lambda x:int(x))
else:
    charge_d=pd.DataFrame({'sid':0,'month':0,'charge_mount':0,'charge_num':0},index=[0])
    
charge_d_grouped=charge_d['charge_mount'].groupby(charge_d['sid']).sum()
charge_d_grouped=charge_d_grouped.reset_index()
# 得到门店的中文名称和每个门店的所有储值金额
charge_d_grouped_m=pd.merge(charge_d_grouped,sname_d,on='sid')
# 刀小蛮的charge_d_grouped_m是空的，他们储值卡都是手工增加后送出去的
if not charge_d_grouped_m.empty:
    fig=plt.figure(3323,figsize=(10,6))
    x=np.arange(charge_d_grouped_m['sname'].count())
    xticks1=charge_d_grouped_m.sort_values(by='charge_mount')['sname']
    c=list(zip(x,charge_d_grouped_m['charge_mount']))
    c.sort(key=itemgetter(1))
    labels,value=zip(*c)
    indexs=np.arange(len(c))
    plt.bar(indexs,value,align='center',width=0.75)
#     plt.xticks(indexs,xticks1,size='small',rotation=45)
    plt.xticks(indexs,xticks1,fontsize=7,rotation=40)

    for a,b in zip(indexs,value):
    #     将标签的字体变大了，如果全部添加的话，重叠太多，所以只选择部分添加标签
        if len(indexs)<20:
            plt.text(a,b+2,'{:,}'.format(b),ha='center',va='bottom',fontsize=10)
        else:
            if a%2==0:
                plt.text(a,b+2,'{:,}'.format(b),ha='center',va='bottom',fontsize=10)
    
    plt.title('各门店总储值金额')
    
    plt.savefig('7门店所有的储值金额',dpi=200)
else :#插入一张空白的figure,在ppt里面去手动删除吧
    fig=plt.figure(3323,figsize=(10,6))
    plt.savefig('7门店所有的储值金额',dpi=200)

# 5.分店的首次充值金额
charge_first='''select t1.sid as sid ,date_format(t1.tcCreated,'%%Y%%m') as 'month',
sum(t1.tcsale/100) as 'first_chargemount',
count(distinct(t2.uid)) as 'first_chargenum'
from welife_trade_charges t1 

inner join(select  uid,min(tccreated) as tccreated from welife_trade_charges 
where bid=%i and  tccreated>%s and tccreated < %s
and tcType=1 and tcStatus=1 and tcChargeType <> 19 group by uid) t2 

on t1.uid=t2.uid and t1.tccreated=t2.tccreated 
group by t1.sid,date_format(t1.tcCreated,'%%Y%%m') ''' %(p.bid,p.ftime_s,p.ftime_e)

# 开始计算每月的再次储值和首次储值
print('5计算首次和再次储值')
charge_first_d=wesql(charge_first)
if charge_first_d.empty:
    charge_first_d=pd.DataFrame({'sid':0,'month':0,'first_chargemount':0,'first_chargenum':0},index=[0])

charge_first_d_grouped=charge_first_d['first_chargemount'].groupby(by=charge_first_d['month']).sum()
charge_first_d_grouped=charge_first_d_grouped.reset_index()

# 拿到上面计算的所有储值
charge_d_grouped_total=charge_d['charge_mount'].groupby(charge_d['month']).sum()
charge_d_grouped_total=charge_d_grouped_total.reset_index()
# 合并计算再次储值
charge_data=pd.merge(charge_d_grouped_total,charge_first_d_grouped,on='month')
charge_data['first_chargemount']=charge_data['first_chargemount'].apply(lambda x:int(x))
charge_data['second_chargemount']=charge_data['charge_mount'].apply(lambda x:int(x))-charge_data['first_chargemount']
charge_data=charge_data.rename(columns={'first_chargemount':'首次储值金额','second_chargemount':'再次储值金额'})
charge_data_list=['首次储值金额','再次储值金额']
double_line2(4, charge_data['month'], charge_data, '月份', '金额(单位:元)', charge_data_list, '每月储值金额的构成')



# 6.储值次数和储值金额的分布
charge_times_money='''select charge_times,count(uid) as pop_num_charge
-- ,sum(charge_real_money) as charge_real_money 
from (
select uid,count(uid) as charge_times,sum(tcsale)/100 as charge_real_money 
from welife_trade_charges
where bid=%i
and tccreated>=%s and tccreated < %s
and tcType=1
and tcStatus=1
group by uid) a 
group by charge_times 
order by charge_times desc''' %(p.bid,p.ftime_s,p.ftime_e)

print('6计算储值次数的转化率')
charge_times_money_d=wesql(charge_times_money)
if charge_times_money_d.empty:
    charge_times_money_d=pd.DataFrame({'charge_times':0,'pop_num_charge':0},index=[0])
# 一商户的储值次数在57次，将小的储值次数全部压缩在一起，所以将次数过滤一下
charge_times_money_d=charge_times_money_d[charge_times_money_d['charge_times']<30]
# 在sql里面根据次数倒序之后，然后求累加，然后在用pandas排序一次
charge_times_money_d['pop_num_charge_cum']=charge_times_money_d['pop_num_charge'].cumsum()
charge_times_money_d=charge_times_money_d.sort_values(by='charge_times')
# 将“次”加在储值次数上
charge_times_money_d['charge_times_ci']=charge_times_money_d['charge_times'].apply(lambda x:str(x))+'次'
# 用窗口函数求出上一行比上下一行，但是此处的rolling函数只能将算出来的值贴在第二行上，所以计算出来的转化率只能从第二次开始画，看图你就明白了
charge_times_money_d['rate']=charge_times_money_d['pop_num_charge_cum'].rolling(2).apply(lambda x:x.min()/x.max())
charge_times_money_d['rate']=charge_times_money_d['rate'].apply(lambda x:float('%.2f' %x))
# w=pd.ExcelWriter('储值人数.xlsx')
# charge_times_money_d.to_excel(w,'data')
# w.save()
# print(charge_times_money_d)
fig=plt.figure(5,figsize=(10,6))

ax2=fig.add_subplot(111)


ax2.bar(charge_times_money_d['charge_times'],charge_times_money_d['pop_num_charge_cum'])
ax2.set_ylabel('储值人数',fontsize=13)

for a,b in zip(charge_times_money_d['charge_times'],charge_times_money_d['pop_num_charge_cum']):
    plt.text(a,b,'{:,}'.format(b),ha='center',va='bottom',fontsize=13)
# 之所以用charge_times来画x是因为这样可以排序，然后用带有‘次’的标签替换掉
plt.xticks(charge_times_money_d['charge_times'],charge_times_money_d['charge_times_ci'])
# 画出双坐标
ax1=ax2.twinx()

ax1.plot(charge_times_money_d['charge_times'],charge_times_money_d['rate'],'r-o')
ax1.set_ylabel('储值次数转化率')
for a,b in zip(charge_times_money_d['charge_times'],charge_times_money_d['rate']):
    plt.text(a,b,'%.0f%%' %(b*100),ha='center',va='bottom',fontsize=12)
ax1.set_title("储值人数和储值次数转化率")    
ax1.set_xlabel('储值次数')
plt.savefig('9储值次数的转化率',dpi=200)



# 7储值档的分布
charge_dist='''select charge_money as charge_line,count(uid) as charge_pop
from(select uid ,tcsale/100 as charge_money,date_format(tccreated,'%%Y%%m%%d') as charge_time
from welife_trade_charges
where tccreated>=%s and tccreated < %s and bid=%i
and tcType=1
and tcStatus=1) a
group by charge_money
order by count(uid) desc 
limit 5''' %(p.ftime_s,p.ftime_e,p.bid)
print('7计算储值人数和金额的比')
charge_dist_d=wesql(charge_dist)
if charge_dist_d.empty:
    charge_dist_d=pd.DataFrame({'charge_line':0,'charge_pop':0},index=[0])
charge_dist_d['charge_money']=charge_dist_d['charge_line']*charge_dist_d['charge_pop']
charge_dist_d['charge_line']=charge_dist_d['charge_line'].apply(lambda x :str(int(x)))
charge_dist_d['charge_line']=charge_dist_d['charge_line']+"档"
charge_dist_d['charge_money']=charge_dist_d['charge_money'].apply(lambda x:int(x))
charge_dist_d['total_pop']=charge_dist_d['charge_pop'].sum()
charge_dist_d['total_money']=charge_dist_d['charge_money'].sum()
charge_dist_d['pop_rate']=charge_dist_d['charge_pop']/charge_dist_d['total_pop']
# charge_dist_d['pop_rate']=charge_dist_d['pop_rate'].apply(lambda x:'%.2f' %x)
charge_dist_d['pop_rate']=charge_dist_d['pop_rate'].apply(lambda x:float(x))

charge_dist_d['money_rate']=charge_dist_d['charge_money']/charge_dist_d['total_money']
# charge_dist_d['money_rate']=charge_dist_d['money_rate'].apply(lambda x:'%.2f' %x)
charge_dist_d['money_rate_m']=charge_dist_d['money_rate'].apply(lambda x:-float(x))

# charge_dist_d储值人数占比低于0.0%的也会画出来，这儿稍微过滤一下
# print(charge_dist_d)
charge_dist_d=charge_dist_d[charge_dist_d['money_rate']>0.01]
charge_dist_d=charge_dist_d[charge_dist_d['pop_rate']>0.01]

# charge_dist_d=charge_dist_d[charge_dist_d['money_rate_m']>0.05]

if not charge_dist_d.empty:
    fig=plt.figure(6,figsize=(10,6))
    X=np.arange(charge_dist_d['charge_line'].count())
    Xlabels=charge_dist_d['charge_line']
    plt.barh(X,charge_dist_d['pop_rate'])
    
    for a,b in enumerate(charge_dist_d['pop_rate']):
        plt.text(b,a,'%.1f%%' %(b*100),ha='left',va='bottom',fontsize=13)
        
    plt.barh(X,charge_dist_d['money_rate_m'])
    for a,b in enumerate(charge_dist_d['money_rate_m']):
        plt.text(b,a,'%.1f%%' %(-b*100),ha='right',va='bottom',fontsize=13)
        
    plt.yticks(X,Xlabels)
    plt.xticks(())
    plt.legend(['储值人数占比','储值金额占比'])
    plt.title('各储值档位上会员的储值情况')
    plt.savefig('10储值档的人数和金额分布',dpi=200)
else:
    fig=plt.figure(6,figsize=(10,6))
    plt.savefig('10储值档的人数和金额分布',dpi=200)

# 8.储值支付方式
charge_type='''select 
round(100*count(case when tcChargeType=1 then uid end)/count(uid),2) '现金',
round(100*count(case when tcChargeType=2 then uid end)/count(uid),2) '银行卡',
round(100*count(case when tcChargeType=4 then uid end)/count(uid),2) '支付宝',
round(100*count(case when tcChargeType=5 then uid end)/count(uid),2) '店内微信',
round(100*count(case when tcChargeType=6 then uid end)/count(uid),2) '手工调账'
from welife_trade_charges 
where bid=%i
and tccreated>=%s and tccreated < %s
and tcType=1
and tcStatus=1'''  %(p.bid,p.ftime_s,p.ftime_e)

print('8计算储值的支付方式')
charge_type_d=wesql(charge_type)
charge_type_d=charge_type_d.T
charge_type_d=charge_type_d.reset_index()
charge_type_d.rename(columns={'index':'type',0:'rate'},inplace=True)
charge_type_d=charge_type_d.sort_values(by='rate')
# 2%以下的几个标签经常产生覆盖，所以先把他们去除掉
charge_type_d=charge_type_d[charge_type_d['rate']>0.02]
fig=plt.figure(9,figsize=(10,6))
plt.pie(charge_type_d['rate'],labels=charge_type_d['type'],autopct='%1.1f%%')
plt.axis('equal')
plt.title('储值支付方式占比')
plt.savefig('11储值支付方式占比')



# 9.消费金额和消费次数的分布，还要能区分等级，只有依据会员的人数来区分
# 首先取出人口最多的3个会员级别，然后将ccid依次的传到下面的消费次数和消费金额里面
# huiyuan_new_create_grid='''select ccid as ccid_n,grid,sum(num) as new_create from(select
# IFNULL(s.ccName,'普通会员') as 'grid',  t.ccid,
# date_format(t.uRegistered, '%%Y%%m') as 'month',
# count(1) num
# from welife%s.welife_users%s t
# left join welife_card_categories s on t.ccid = s.ccid
# where t.bid =%i
# and t.uCardStatus=2
# group by s.ccName,date_format(t.uRegistered,'%%Y%%m'))a 
# group by ccid,grid
# order by new_create desc limit 3 '''  %(p.dbs,p.tbs,p.bid)
# huiyuan_new_create_grid_d=wesql(huiyuan_new_create_grid)




# 之前用的是新增排前3的等级来计算消费能力，结果有些新增在前的反而并没有消费记录，
# 明显的就是普通会员，所以现在用消费人数在前3的等级来计算消费能力
vip_consume_grid='''select grid as ccid,count(uid) as num
from dprpt_welife_trade_consume_detail
where ftime>%s and ftime<%s and bid=%i and tctype=2
group by grid
order by num desc 
limit 3''' %(p.ftime_s,p.ftime_e,p.bid)
vip_consume_grid=dwsql(vip_consume_grid)


# 这儿要注意的是，在注册表里面的普通会员的等级可能会是0，而消费表里面没有，所以先拿出注册表里面的会员等级的中文名，
# 和category里面的匹配，然后拿到完整的，grid,在传入到下面的消费次数和金额分布里面
huiyuan_new_create_grid_d=pd.merge(vip_consume_grid,ccname_d,on='ccid')
# print(huiyuan_new_create_grid_d)

# print(huiyuan_new_create_grid_d)
# del huiyuan_new_create_grid_d['ccid_n']
ccid=dict(huiyuan_new_create_grid_d[['ccid','grid']].values)
print('9计算消费次数和金额的分布')
for ci, cn in ccid.items():

#     消费次数的分布
    consume_num_distribute='''select 
    count(case when tctotalfee/100>0 and tctotalfee/100<=50 then uid end) '0-50',
    count(case when tctotalfee/100>50 and tctotalfee/100<=100 then uid end) '50-100',
    count(case when tctotalfee/100>100 and tctotalfee/100<=150 then uid end) '100-150',
    count(case when tctotalfee/100>150 and tctotalfee/100<=200 then uid end) '150-200',
    count(case when tctotalfee/100>200 and tctotalfee/100<=250 then uid end) '200-250',
    count(case when tctotalfee/100>250 and tctotalfee/100<=300 then uid end) '250-300',
    count(case when tctotalfee/100>300 and tctotalfee/100<=350 then uid end) '300-350',
    count(case when tctotalfee/100>350 and tctotalfee/100<=400 then uid end) '350-400',
    count(case when tctotalfee/100>400 and tctotalfee/100<=450 then uid end) '400-450',
    count(case when tctotalfee/100>450 and tctotalfee/100<=500 then uid end) '450-500',
    count(case when tctotalfee/100>500 and tctotalfee/100<=550 then uid end) '500-550',
    count(case when tctotalfee/100>550 and tctotalfee/100<=600 then uid end) '550-600',
    count(case when tctotalfee/100>600 and tctotalfee/100<=650 then uid end) '600-650',
    count(case when tctotalfee/100>650 and tctotalfee/100<=700 then uid end) '650-700',
    count(case when tctotalfee/100>700 and tctotalfee/100<=750 then uid end) '700-750',
    count(case when tctotalfee/100>750 and tctotalfee/100<=800 then uid end) '750-800',
    count(case when tctotalfee/100>800 and tctotalfee/100<=850 then uid end) '800-850',
    count(case when tctotalfee/100>850 and tctotalfee/100<=900 then uid end) '850-900',
    count(case when tctotalfee/100>900 and tctotalfee/100<=950 then uid end) '900-950',
    count(case when tctotalfee/100>950 and tctotalfee/100<=1000 then uid end) '950-1000',
    count(case when tctotalfee/100>1000 and tctotalfee/100<=1500 then uid end) '1000-1500',
    count(case when tctotalfee/100>1500 then uid end) '1500-99999'
    from dprpt_welife_trade_consume_detail      
    where ftime>=%s
    and ftime<%s 
    and bid=%i
    and grid=%i
    and tctype=2'''  %(p.ftime_s,p.ftime_e,p.bid,ci)
    consume_num_distribute_d=dwsql(consume_num_distribute)
    consume_num_distribute_d=consume_num_distribute_d.T
#     print(consume_num_distribute_d)

# 消费金额的分布
    consume_money_dist='''select 
    sum(case when tctotalfee/100>0 and tctotalfee/100<=50 then tctotalfee/100 end)/sum(tctotalfee/100) '0-50',
    sum(case when tctotalfee/100>50 and tctotalfee/100<=100 then tctotalfee/100 end)/sum(tctotalfee/100) '50-100',
    sum(case when tctotalfee/100>100 and tctotalfee/100<=150 then tctotalfee/100 end)/sum(tctotalfee/100) '100-150',
    sum(case when tctotalfee/100>150 and tctotalfee/100<=200 then tctotalfee/100 end)/sum(tctotalfee/100) '150-200',
    sum(case when tctotalfee/100>200 and tctotalfee/100<=250 then tctotalfee/100 end)/sum(tctotalfee/100) '200-250',
    sum(case when tctotalfee/100>250 and tctotalfee/100<=300 then tctotalfee/100 end)/sum(tctotalfee/100) '250-300',
    sum(case when tctotalfee/100>300 and tctotalfee/100<=350 then tctotalfee/100 end)/sum(tctotalfee/100) '300-350',
    sum(case when tctotalfee/100>350 and tctotalfee/100<=400 then tctotalfee/100 end)/sum(tctotalfee/100) '350-400',
    sum(case when tctotalfee/100>400 and tctotalfee/100<=450 then tctotalfee/100 end)/sum(tctotalfee/100) '400-450',
    sum(case when tctotalfee/100>450 and tctotalfee/100<=500 then tctotalfee/100 end)/sum(tctotalfee/100) '450-500',
    sum(case when tctotalfee/100>500 and tctotalfee/100<=550 then tctotalfee/100 end)/sum(tctotalfee/100) '500-550',
    sum(case when tctotalfee/100>550 and tctotalfee/100<=600 then tctotalfee/100 end)/sum(tctotalfee/100) '550-600',
    sum(case when tctotalfee/100>600 and tctotalfee/100<=650 then tctotalfee/100 end)/sum(tctotalfee/100) '600-650',
    sum(case when tctotalfee/100>650 and tctotalfee/100<=700 then tctotalfee/100 end)/sum(tctotalfee/100) '650-700',
    sum(case when tctotalfee/100>700 and tctotalfee/100<=750 then tctotalfee/100 end)/sum(tctotalfee/100) '700-750',
    sum(case when tctotalfee/100>750 and tctotalfee/100<=800 then tctotalfee/100 end)/sum(tctotalfee/100) '750-800',
    sum(case when tctotalfee/100>800 and tctotalfee/100<=850 then tctotalfee/100 end)/sum(tctotalfee/100) '800-850',
    sum(case when tctotalfee/100>850 and tctotalfee/100<=900 then tctotalfee/100 end)/sum(tctotalfee/100) '850-900',
    sum(case when tctotalfee/100>900 and tctotalfee/100<=950 then tctotalfee/100 end)/sum(tctotalfee/100) '900-950',
    sum(case when tctotalfee/100>950 and tctotalfee/100<=1000 then tctotalfee/100 end)/sum(tctotalfee/100) '950-1000',
    sum(case when tctotalfee/100>1000 and tctotalfee/100<=1500 then tctotalfee/100 end)/sum(tctotalfee/100) '1000-1500',
    sum(case when tctotalfee/100>1500 then  tctotalfee/100 end)/sum(tctotalfee/100) '1500-99999'
    from dprpt_welife_trade_consume_detail
    where ftime>=%s
    and ftime<%s
    and bid=%i
    and grid=%i
    and tctype=2 ''' %(p.ftime_s,p.ftime_e,p.bid,ci)
    
    consume_money_dist=dwsql(consume_money_dist)
    consume_money_dist=consume_money_dist.T
#     print(consume_money_dist)
    
#     将消费次数和消费区间合并
    re2=pd.merge(consume_num_distribute_d,consume_money_dist,left_index=True,right_index=True)
    re2=re2.reset_index()
#     更改数据的列名
    re2.rename(columns={'index':'区间','0_x':'消费人数','0_y':'消费金额占比'},inplace=True)
#     要是有等于0的行在里面的话，消费金额占比进行apply时由于nonetype就无法通过
    re2=re2[re2['消费人数']>0]
#     将消费金额占比保留两位小数
    re2['消费金额占比']=re2['消费金额占比'].apply(lambda x:float('%.2f' %x))
    d_s=[]
#     这儿有个小问题就是50-100这个区间很喜欢跑到中间，所以人为的将它分割之后，根据前面的数据排列，如50-100就取出50
    for i in re2['区间']:
        d=int(i.split('-')[0])
        d_s.append(d)
    re2['inteval']=d_s
    re3=re2.sort_values(by='inteval')
#     print(re3)
#     制作X轴和X轴的标签
    la=np.arange(re3['区间'].count())
    xla=re3['区间']
    
    
#     这儿之所以传入ci,是为了防止将图画在同一个fig上
    fig=plt.figure('%i' %ci,figsize=(9,6))
    ax11=fig.add_subplot(111)
    
#     柱状图bar_p后面不需要,line_p的后面才需要
    bar_p=ax11.bar(la,re3['消费金额占比'])
    for a,b in zip(la,re3['消费金额占比']):
        if  a%2!=0:
            plt.text(a,b+0.004,'%.2f%%'%(b*100),ha='center',va='bottom',fontsize=13)
    
    ax11.set_ylabel('消费金额占比')
#     ax11.set_xlabel('消费区间')
    ax11.set_title('%s的消费能力' %cn)
#     ax11.legend('消费金额占比')
    plt.xticks(la,xla,size='small',rotation=45)
    
#     双坐标抽
    ax22=ax11.twinx()
    line_p,=ax22.plot(la,re3['消费人数'],'r-o',label='消费人数')
    for a,b in zip(la,re3['消费人数']):
        if a%2==0:
            plt.text(a,b,'{:,}'.format(b),ha='center',va='bottom',fontsize=13)        
    ax22.set_ylabel('消费人数')
#     ax22.legend(['消费人数'])
    plt.legend([bar_p,line_p],['消费金额占比','消费人数'])
    plt.title('%s的消费能力' %cn)
    print(cn,ci)
#     plt.savefig('12_%s消费能力%i' %(cn,ci))
    plt.savefig('12_消费能力%i' %(ci))





# # 10.各储值档消耗完所用的时间
# charge_consume_time='''select 
# case when tcruleid='' then 0 when tcruleid is null then 0 else tcruleid end tcruleid,
# if(sum(diff) is null,0,sum(diff))/if(count(1)=0,1,count(1)) ctime
# from (select uid,tcruleid,datediff(max(tcCreated),min(tcCreated)) diff
# from (SELECT a.uid,a.tcruleid,a.tcCreated 
# FROM welife_trade_charges a 
# WHERE bid=%i
# and tctype=1 and tcCreated>20170501 and tcCreated<20180101
# and (SELECT COUNT(*) FROM welife_trade_charges WHERE bid=%i and tctype=1 and uid = a.uid AND tcCreated < a.tcCreated ) < 2 
# ORDER BY a.uid,a.tcruleid,a.tcCreated) t
# group by uid,tcruleid) s
# where diff>0
# group by s.tcruleid'''   %(p.bid,p.bid)
# 
# charge_consume_time_d=wesql(charge_consume_time)
# print(charge_consume_time_d)
# 
# 
# # 储值档的中文名称
# chrules='''select t.crName crName,s.crlRuleIds tcruleid,s.crlRule crlRule
# from welife_charge_rule_logs s ,welife_charge_rules t 
# where s.bid=%i
# and s.crlRuleId = t.crId'''   %(p.bid)
# chrules_d=wesql(chrules)
# chrules_d['crlRule_con']=chrules_d['crlRule']+'-'+chrules_d['crName']
# # print(chrules_d)
# 
# 
# charge_consume_time_d_rules=pd.merge(charge_consume_time_d,chrules_d,on='tcruleid',how='left')
# print(charge_consume_time_d_rules)
# 
# 
# fig, ax = plt.subplots()
# ax.bar(np.arange(len(charge_consume_time_d_rules['crlRule_con'])),charge_consume_time_d_rules['ctime'])
# # print(charge_consume_time_d_rules)
# lables=ax.get_xtickslabes()
# 
# plt.show()


# 11.储值会员续充的时间间隔
xuchong_time='''select uid,charge_time,
@x:=if(@user_uid=uid,@x+1,1) as rank,
@user_uid:=uid as dummy
from 
(select a1.uid,date_format(tcCreated,'%%Y%%m%%d') as charge_time
from ( select uid,tcCreated from welife_trade_charges
where bid=%i  and tcType=1 and tcStatus=1) a1 
inner join (select uid from welife_user_savings where bid=%i and usChargeCount>1) a2 on a1.uid=a2.uid ) t1,
(select @x:=0,@y:=0,@user_uid:=null) t2 '''  %(p.bid,p.bid)
xuchong_time_d=wesql(xuchong_time)
if len(xuchong_time_d)>10 : #如果len很小的话，下面也会报错
# 首充时间
    first_charge_time=xuchong_time_d[xuchong_time_d['rank']==1]
    # 续充时间
    second_charge_time=xuchong_time_d[xuchong_time_d['rank']==2]
    
    # 第三次储值时间，本打算求出2次和3次储值的时间间隔，发现目前还没有必要细致到那个程度，先留着
    # third_charge_time=xuchong_time_d[xuchong_time_d['rank']==3]
    
    # 合并第一次储值和第二次储值时间
    first_charge_time_and_second_charge_time=pd.merge(first_charge_time,second_charge_time,on='uid')
    first_charge_time_and_second_charge_time['ftime_1']=first_charge_time_and_second_charge_time['charge_time_x'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
    first_charge_time_and_second_charge_time['ftime_2']=first_charge_time_and_second_charge_time['charge_time_y'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
    
    
    
    first_charge_time_and_second_charge_time['interval']=first_charge_time_and_second_charge_time['ftime_2']-first_charge_time_and_second_charge_time['ftime_1']
    # 两次充值的时间差有负数，两次充值的时间会互换，所以用了np.abs求绝对值np.abs(x.days))
    first_charge_time_and_second_charge_time['days']=first_charge_time_and_second_charge_time['interval'].apply(lambda x:np.abs(x.days))
    a_max=first_charge_time_and_second_charge_time['days'].max()
   
    a_min=first_charge_time_and_second_charge_time['days'].min()
#     print(a_min); print(a_max)
#     cut_points=[a_min,30,60,90,120,a_max]
#     mylabels=['%s-30天'%a_min,'31-60天','61-90天','91-120天','121-%s天'%a_max]

#     cut_points=[a_min,a_max]
#     mylabels=['%s_%s天' %(a_min,a_max)]
    
    cut_points=[a_min,a_max/4,a_max/2,a_max]
    mylabels=['%s_%s天' %(a_min,int(a_max/4)),'%s-%s天'%(int(a_max/4),int(a_max/2)),'%s_%s天'%(int(a_max/2),a_max)]
#     print(first_charge_time_and_second_charge_time['days'])
    first_charge_time_and_second_charge_time['panduan']=pd.cut(first_charge_time_and_second_charge_time['days'],cut_points,labels=mylabels)
    first_and_second_charge_mean_day=first_charge_time_and_second_charge_time['days'].mean()
    charge_interval_pivot=pd.pivot_table(first_charge_time_and_second_charge_time,index='panduan',values='uid',aggfunc=len,fill_value=0)
    
    fig=plt.figure(40,figsize=(10,6))
    plt.pie(charge_interval_pivot['uid'],labels=charge_interval_pivot.index,autopct='%1.1f%%')
    plt.axis('equal')
    plt.title('首次储值与再次储值间隔时间人数分布 \n \n 首次和再次储值平均间隔%s天'%int(first_and_second_charge_mean_day))
    plt.savefig('40首次储值与再次储值间隔时间人数分布')
else:
    fig=plt.figure(40,figsize=(10,6))
    plt.bar(0,0)
    plt.title('需要删除')
    plt.savefig('40首次储值与再次储值间隔时间人数分布')



# close()






