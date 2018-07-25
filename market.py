#-*- coding:utf-8 -*-
#"2018年1月14日"
from connect.connect import dwsql,wesql,pd,close
import matplotlib.pyplot as plt 
from  datetime import datetime
import numpy as np
from pandas_pptx import public as p
from pandas_pptx.method_old import bing,xuanf2,autolabel_size,autolabel,bar_h


print('=========================')
print('market')
print('=========================')


plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号



# 1.优惠券营销活动
coupon_use='''select aid '编号',
couponid '券ID',
activityname '活动名称',
couponname '券名称',
sum(couponsendsum) '发券量',
sum(couponusedsum) '使用券量',
sum(tradecash - cancelcash)/100 '拉动现金消费',
sum(camount * couponusedsum)/100 '拉动券消费',
sum(tradeprepay - canceltradepv)/100 '拉动储值消费',
concat(round(100*sum(couponusedsum)/sum(couponsendsum),2),'%%') '使用率'
from dprpt_welife_activity_log 
where bid=%i
and ftime>=%s
and ftime<%s 
group by activityname,couponname''' %(p.bid,p.ftime_s,p.ftime_e)
print('1计算营销收入')
coupon_use_d=dwsql(coupon_use)

coupon_use_d=coupon_use_d.fillna(0)
# print(coupon_use_d.head())
if coupon_use_d.empty or coupon_use_d['发券量'].max()<=0:
    fig=plt.figure(29)
    plt.bar(0,0)
    plt.legend('需要删除')
    plt.savefig('29发券量靠前的券使用率')
else:
  #如果没有营销活动的话，就在下面插入一张空的图片，然后手动删除
    coupon_use_d['拉动总消费']=coupon_use_d['拉动现金消费']+coupon_use_d['拉动券消费']+coupon_use_d['拉动储值消费']
    # consume_sum求和之后变成一个数据框
    consume_sum=pd.DataFrame({'拉动总消费':coupon_use_d['拉动总消费'].sum()},index=[0])
    # print(consume_sum)
    # 想要计算营销收入占总营业额的比重，所以还要知道总的营业额
    consume_money=''' select sum(tctotalfee/100) as 消费金额
    from dprpt_welife_trade_consume_detail 
    where bid=%i and tctype=2 and  ftime>=%s and ftime<%s  ''' %(p.bid,p.ftime_s,p.ftime_e)
    consume_money_d=dwsql(consume_money)
    # print('consume_money_d',consume_money_d)
    
    print('1.1计算营销收入占总收入的比')
    market_re=pd.concat([consume_sum,consume_money_d],axis=1)
    market_re['非营销拉动']=market_re['消费金额']-market_re['拉动总消费']
    market_re2=market_re[['拉动总消费','非营销拉动']].T.reset_index().rename(columns={'index':'type',0:'value'})
    # print(market_re2)
    bing(27,market_re2['value'],market_re2['type'],'营销收入占总会员收入的比')
    
    print('1.2各券带来的收入')
    # 从券的角度来看各张券带来的收入占比
    coupon_use_d_coupon=pd.pivot_table(coupon_use_d,index=['券名称'],values=['发券量','使用券量','拉动总消费'],aggfunc=np.sum)
    coupon_use_d_coupon=coupon_use_d_coupon.reset_index()
    # 根据拉动的总消费排序，然后取出值最大的前5项
    # 有些垃圾券的数据为0，所以要剔除，否则没法apply(lambda x:int(x))
    coupon_use_d_coupon=coupon_use_d_coupon[coupon_use_d_coupon['拉动总消费']>0]
    coupon_use_d_coupon['拉动总消费']=coupon_use_d_coupon['拉动总消费'].apply(lambda x:int(x))
    coupon_use_d_coupon_1=coupon_use_d_coupon.sort_values(by='拉动总消费',ascending=False)
    
    coupon_use_d_coupon_1_top_5=coupon_use_d_coupon_1.head(3)
    # print(coupon_use_d_coupon_1_top_5)
    bing(28,coupon_use_d_coupon_1_top_5['拉动总消费'],coupon_use_d_coupon_1_top_5['券名称'],'收益最高3张券带动营业额占比')
    
    # 通常开卡礼所占的比例过高，现在把开卡礼拿掉之后，再来看个券的占比，默认开卡礼带来的消费金额最多，所以拿掉最大值之后剩下的就是排除开卡里之后的
    coupon_use_d_coupon_1_top_5_no_kaikali=coupon_use_d_coupon_1[coupon_use_d_coupon_1['拉动总消费']<coupon_use_d_coupon_1['拉动总消费'].max()]
    coupon_use_d_coupon_1_top_5_no_kaikali_top_5=coupon_use_d_coupon_1_top_5_no_kaikali.head(6)
    # print(coupon_use_d_coupon_1_top_5_no_kaikali_top_5.head())
    bing(42,coupon_use_d_coupon_1_top_5_no_kaikali_top_5['拉动总消费'],coupon_use_d_coupon_1_top_5_no_kaikali_top_5['券名称'],'除开卡礼外收益较高券带动营业额占比')
    
    
    
    
    
    
    
    print('1.3发券量最高的10张券的使用情况')
    # 根据发券量排序，然后取出值最大的前10项
    coupon_use_d_coupon_2=coupon_use_d_coupon.sort_values(by='发券量',ascending=False)
    if len(coupon_use_d_coupon_2)>=10:
        coupon_use_d_coupon_2_top_10=coupon_use_d_coupon_2.head(10)
    else:
        coupon_use_d_coupon_2_top_10=coupon_use_d_coupon_2.head(5)
    
    coupon_use_d_coupon_2_top_10_new=coupon_use_d_coupon_2_top_10.copy()
    # 即使选择了前5依然有发券量为0的存在，所以直接筛选大于0的
    coupon_use_d_coupon_2_top_10_new=coupon_use_d_coupon_2_top_10_new[coupon_use_d_coupon_2_top_10_new['发券量']>0]
    coupon_use_d_coupon_2_top_10_new['使用率']=coupon_use_d_coupon_2_top_10_new['使用券量']/coupon_use_d_coupon_2_top_10_new['发券量']
    
    # 在xuanf2里面的两个柱子之间的量纲,用size 表示，这个地方求的时候经常decimal和float的错误，所以先将使用率扩大100倍之后
    # 再和发券量相比，这样做整数之间的除法
    # print(coupon_use_d_coupon_2_top_10_new)
    # print('使用率均值',coupon_use_d_coupon_2_top_10_new['使用率'].min())
    
    
    
    if coupon_use_d_coupon_2_top_10_new['使用率'].min()>0.01:
        coupon_use_d_coupon_2_top_10_new['使用率n']=coupon_use_d_coupon_2_top_10_new['使用率'].apply(lambda x:int(x*100))
        a=coupon_use_d_coupon_2_top_10_new['发券量']/coupon_use_d_coupon_2_top_10_new['使用率n']
    # b 就是xuanf2里面的size,但是如果将b扩大到100倍的话，画出来的不好看，所以暂时扩大10倍
        b=int(a.mean())*10
    else:
        coupon_use_d_coupon_2_top_10_new['使用率n']=coupon_use_d_coupon_2_top_10_new['使用率'].apply(lambda x:int(x*1000))
        coupon_use_d_coupon_2_top_10_new=coupon_use_d_coupon_2_top_10_new[coupon_use_d_coupon_2_top_10_new['使用率n']>0]
        a=coupon_use_d_coupon_2_top_10_new['发券量']/coupon_use_d_coupon_2_top_10_new['使用率n']
    # b 就是xuanf2里面的size,但是如果将b扩大到100倍的话，画出来的不好看，所以暂时扩大10倍
        if a.empty:
            b=100
        else:
            b=int(a.mean())*1000
    if coupon_use_d_coupon_2_top_10_new.empty:
        fig=plt.figure(29)
        plt.bar(0,0)
        plt.title('需要删除')
        plt.savefig('29发券量靠前的券使用率')
    else:
        print(coupon_use_d_coupon_2_top_10_new)
        xuanf2(29, coupon_use_d_coupon_2_top_10_new['券名称'], coupon_use_d_coupon_2_top_10_new['发券量'],
               coupon_use_d_coupon_2_top_10_new['使用率'], b, '发券量靠前的券使用率', '发券量', '使用率')

    


# 2.积分营销
# 积分的使用人数(这里是依照grid分组求的，做图时候可以只算全部的使用率)
point_use_grid='''select count(distinct(case when a.sendpoint > 0 then a.uid end)) '积分发放人数',
count(distinct(case when pointpay > 0  then a.uid end)) '积分使用人数'
-- ,concat(round(100*count(distinct(case when a.pointpay > 0 then a.uid end))/count(distinct(a.uid)),2),'%%') '使用积分抵扣占比'
from dprpt_welife_trade_consume_detail a
where bid=%i
and tctype=2 
and ftime>=%s
and ftime<%s ''' %(p.bid,p.ftime_s,p.ftime_e)
print('2.积分使用人数')
point_use_grid_d=dwsql(point_use_grid)
point_use_grid_d=point_use_grid_d.T.reset_index()
# print(point_use_grid_d)



#积分的使用数量
point_use_number='''select  
sum(case when t.tctradetype = 1 then t.tccredit end) 发放积分,
sum(case when t.tctradetype = 2 then t.tccredit end) 使用积分
-- concat(round(100*sum(case when t.tctradetype = 2 then t.tccredit end)/sum(case when t.tctradetype = 1 then t.tccredit end),2),'%%') '积分消耗占比'
from welife_trade_credit t
where bid=%i
and tcCreated >= %s
and tcCreated < %s ''' %(p.bid,p.ftime_s,p.ftime_e)
print('3.积分使用数量')
point_use_number_d=wesql(point_use_number)
point_use_number_d=point_use_number_d.T.reset_index()

# 有时积分的使用数量为0，所以还要替换一下
point_use_number_d[0]=point_use_number_d[0].where(point_use_number_d[0].notnull(),0)

fig=plt.figure(30,figsize=(10,6),dpi=200)
ax1=plt.subplot(121)
ax1.bar(point_use_grid_d['index'],point_use_grid_d[0])
autolabel(point_use_grid_d['index'],point_use_grid_d[0],12)
plt.title('积分发放和使用人数')
ax=plt.subplot(122)
ax3=ax.twinx()
ax3.bar(point_use_number_d['index'],point_use_number_d[0])
autolabel(point_use_number_d['index'],point_use_number_d[0],12)
ax.set_yticks(())
plt.title('积分发放和使用数量')
plt.savefig('31积分使用人数和数量')



# 3.积分的余额分布
#-------------26.积分余额分布
point_saving='''select 
count(case when utcSaving=1 then uid end) '1',
count(case when utcSaving=2 then uid end) '2',
count(case when utcSaving=3 then uid end) '3',
count(case when utcSaving=4 then uid end) '4',
count(case when utcSaving=5 then uid end) '5',
count(case when utcSaving=6 then uid end) '6',
count(case when utcSaving=7 then uid end) '7',
count(case when utcSaving=8 then uid end) '8',
count(case when utcSaving=9 then uid end) '9',
count(case when utcSaving=10 then uid end) '10',
count(case when utcSaving=11 then uid end) '11',
count(case when utcSaving=12 then uid end) '12',
count(case when utcSaving=13 then uid end) '13',
count(case when utcSaving=14 then uid end) '14',
count(case when utcSaving=15 then uid end) '15',
count(case when utcSaving=16 then uid end) '16',
count(case when utcSaving=17 then uid end) '17',
count(case when utcSaving=18 then uid end) '18',
count(case when utcSaving=19 then uid end) '19',
count(case when utcSaving=20 then uid end) '20',
count(case when utcSaving>20 and utcSaving<=30 then uid end) '21-30',
count(case when utcSaving>30 and utcSaving<=40 then uid end) '31-40',
count(case when utcSaving>40 and utcSaving<=50 then uid end) '41-50',
count(case when utcSaving>50 and utcSaving<=100 then uid end) '51-100',
count(case when utcSaving>100 and utcSaving<=200 then uid end) '101-200',
count(case when utcSaving>200 and utcSaving<=300 then uid end) '201-300',
count(case when utcSaving>300 and utcSaving<=400 then uid end) '301-400',
count(case when utcSaving>400 and utcSaving<=500 then uid end) '401-500',
count(case when utcSaving>500 then uid end) '501-9999'
from 
(select uid,sum(utcSaving) utcSaving
from welife_user_trade_credit
where bid=%i
and utcStatus in (1,2)
group by uid) t''' %p.bid
print('4.积分余额分布')
point_saving_d=wesql(point_saving)
point_saving_d=point_saving_d.T.reset_index()
# 因为里面有个‘501以上’，这个选项让后面的排序很难进行，所以直接将余额小于0的过滤掉，估计也很少有人的积分余额能够高于500
point_saving_d=point_saving_d[point_saving_d[0]>0]
# print(point_saving_d)

d_n=[]
# 仿照消费能力里面的，将’200-300‘这样的字段提取出200，然后排序
for i in point_saving_d['index']:
#     之所以要大于1是因为，即使没有‘-’也可以找出一个值
    if i.find('-')>1:
        d=i.split('-')[0]
        d_n.append(d)
    else:
        d_n.append(i)
d_n2=[int(x) for x in d_n]   
# 将新取出来的列，合并到原有的数据框里面
point_saving_d['new']=d_n2
point_saving_d_sort=point_saving_d.sort_values(by='new')
# print(point_saving_d_sort) 
# 开始画图  
index_2=np.arange(len(point_saving_d_sort))   


fig=plt.figure(31,figsize=(10,6),dpi=200)
plt.bar(index_2,point_saving_d_sort[0])
for a,b in zip(index_2,point_saving_d_sort[0]):
    if a%2==0:
        plt.text(a,b,'{0}'.format(int(b)),ha='center',va='baseline',fontsize=10)
plt.xticks(index_2,point_saving_d_sort['index'],fontsize=8,rotation=35)
plt.ylabel('人数')
plt.title('积分余额的分布')
plt.savefig('31积分余额的分布')



# 4.是否使用积分的差异
point_used='''select 
sum(case when sumpoint>0 then sumfee end)/count(case when sumpoint>0 then uid end) '人均_使用',
sum(case when sumpoint>0 then sumfee end)/sum(case when sumpoint>0 then trade_num end) '桌均_使用',
sum(case when sumpoint>0 then trade_num end)/count(case when sumpoint>0 then uid end) '均次_使用',
sum(case when sumpoint=0 and sumsend>0 then sumfee end)/count(case when sumpoint=0 and sumsend>0 then uid end) '人均_未用',
sum(case when sumpoint=0 and sumsend>0 then sumfee end)/sum(case when sumpoint=0 and sumsend>0 then trade_num end) '桌均_未用',
sum(case when sumpoint=0 and sumsend>0 then trade_num end)/count(case when sumpoint=0 and sumsend>0 then uid end) '均次_未用'
from (select uid,sum(pointpay) sumpoint,count(uid) trade_num,sum(tctotalfee/100) sumfee,sum(sendpoint) sumsend 
from dprpt_welife_trade_consume_detail 
where bid=%s and tctype=2 and ftime>=%s and ftime<=%s
group by uid) a 
where trade_num>=2'''  %(p.bid,p.ftime_s,p.ftime_e)
point_used_d=dwsql(point_used)

point_used_d=point_used_d.fillna(0)

point_used_d_t=point_used_d.T
point_d1=pd.DataFrame(point_used_d_t.ix[['人均_使用','人均_未用'],0])
point_d2=pd.DataFrame(point_used_d_t.ix[['桌均_使用','桌均_未用'],0])
point_d3=pd.DataFrame(point_used_d_t.ix[['均次_使用','均次_未用'],0])




fig=plt.figure(35,figsize=(10,6),dpi=200)


# ax1=fig.add_subplot(131)
# ax1.bar(point_d1.index,point_d1[0])
# for a,b in zip(point_d1.index,point_d1[0]):
#     plt.text(a,b,'{:,}'.format(int(b)),ha='center',va='baseline',fontsize=11)


# ax2=fig.add_subplot(132)
ax2=fig.add_subplot(121)

ax2.bar(point_d2.index,point_d2[0])
for a,b in zip(point_d2.index,point_d2[0]):
    plt.text(a,b,'{:,}'.format(int(b)),ha='center',va='baseline',fontsize=11)
plt.title('是否使用积分的差异')
plt.yticks(())

# ax3=fig.add_subplot(133)
ax3=fig.add_subplot(122)

ax3.bar(point_d3.index,point_d3[0])
for a,b in zip(point_d3.index,point_d3[0]):
    plt.text(a,b,'{:,}'.format(int(b)),ha='center',va='baseline',fontsize=11)
plt.savefig('35是否使用积分的差异')






# close()














