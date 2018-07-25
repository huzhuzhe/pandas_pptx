#-*- coding:utf-8 -*-
#"2018年1月31日"

print('==============================')
print('取消关注')
print('==============================')




from connect.connect import dwsql,wesql,pd,close
import numpy as np
from  datetime import datetime
import matplotlib.pyplot as plt 
from pandas_pptx.canlce_method import cxuanf1,cbar_h2,cmycut,cxuanf,cbing,cline_h1,cline_h,cxuanf3,cautolabel_size,cxuanf2,cline_h11,cxuanf22,cbing1,cbar_h22
from pandas_pptx import public as p


plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号



# 1.各等级每月新增（有几个会员等级就画几张图出来）包括取消关注的
huiyuan_new_create_grid='''select grid,month,sum(num) as new_create from(select
IFNULL(s.ccName,'普通会员') as 'grid',  
date_format(t.uRegistered, '%%Y%%m') as 'month',
count(1) num
from welife%s.welife_users%s t
left join welife_card_categories s on t.ccid = s.ccid
where t.bid =%i
and t.uRegistered >= %s
and t.uRegistered < %s
-- and t.uCardStatus=2
group by s.ccName,date_format(t.uRegistered,'%%Y%%m'))a group by grid,month'''  %(p.dbs,p.tbs,p.bid,p.ftime_s,p.ftime_e)

print('1.整体会员新增')
huiyuan_new_create_grid_d=wesql(huiyuan_new_create_grid)
# 获得整体会员每月的发展情况
huiyuan_new_create_grid_d_grouped=huiyuan_new_create_grid_d.groupby('month').sum()

# 取消索引，便于直接对列做出引用
huiyuan_new_create_grid_d_grouped=huiyuan_new_create_grid_d_grouped.reset_index()
huiyuan_new_create_grid_d_grouped['new_create']=huiyuan_new_create_grid_d_grouped['new_create'].apply(lambda x:int(x))
# print(huiyuan_new_create_grid_d_grouped)
huiyuan_new_create_grid_d_grouped['change']=huiyuan_new_create_grid_d_grouped['new_create'].pct_change()
# print(huiyuan_new_create_grid_d_grouped)


# cxuanf1(1, huiyuan_new_create_grid_d_grouped['month'], huiyuan_new_create_grid_d_grouped['new_create'], 
#        huiyuan_new_create_grid_d_grouped['change'], '每月会员的新增以及环比变化', '新增变化','环比',8)


# 2.每月取消关注的数量
# 每月取消关注的数量
cancle_user='''select 
date_format(t.uUnRegistered, '%%Y%%m') as 'unmonth',
count(distinct(uid)) as cancle_num
from welife%s.welife_users%s t
where t.bid =%i and t.uCardStatus=3
and date_format(t.uUnRegistered, '%%Y%%m%%d')>=%s and date_format(t.uUnRegistered, '%%Y%%m%%d')<%s
group by unmonth''' %(p.dbs,p.tbs,p.bid,p.ftime_s,p.ftime_e)
print('2.每月取消关注')
cancle_user_d=wesql(cancle_user)
# 有点奇怪的是月份是000000，于是将月份变成整数之后再进行筛选
cancle_user_d['unmonth2']=cancle_user_d['unmonth'].apply(lambda x:int(x))
cancle_user_d=cancle_user_d[cancle_user_d['unmonth2']>0]
# print(cancle_user_d)
cancle_user_d['change']=cancle_user_d['cancle_num'].pct_change()
# 取关的数据是后来新增的，所在在figure上统一添加了今天的日期3月23号
cxuanf1(3232, cancle_user_d['unmonth'], cancle_user_d['cancle_num'], cancle_user_d['change'], '每月取消关注的数量以及环比变化',
        '取关人数', '环比', 15)


# 2.1计算每月取消关注的人数占每月新增人数的比
#         2.11获取每月的新增,将多余的列裁掉了
new_create_month=huiyuan_new_create_grid_d_grouped[['month','new_create']]
my_re=pd.merge(new_create_month,cancle_user_d,left_on='month',right_on='unmonth')
# 计算取关占新增的比
my_re['rate']=my_re['cancle_num']/my_re['new_create']
cline_h11(3237, my_re['month'], my_re['rate'], '每月取关人数占新增的比',13)


# 3.取消关注前一共的消费次数和消费金额
cancle_user_consume='''select t_gap,total_consumes_num,count(distinct(uno)) as number
from (
select  uno,datediff(uUnRegistered, uregistered) as t_gap,uConsumeNum as total_consumes_num
from welife%s.welife_users%s
where bid=%i and  date_format(uRegistered, '%%Y%%m%%d')>=%s and date_format(uRegistered, '%%Y%%m%%d')<%s
and uCardStatus=3) a
group by t_gap,total_consumes_num''' %(p.dbs,p.tbs,p.bid,p.ftime_s,p.ftime_e)

print('3.取消关注的消费情况')
cancle_user_consume_d=wesql(cancle_user_consume)

# 当uCardStatus=3的时候，有些会员没有取消关注的时间，依据亮哥的说法，是因为导入的用户有注册时间，没有取消关注的时间，
# 也就是这些用户之间就已经取消关注了,所以让间隔时间大于0以过滤这批用户
cancle_user_consume_d=cancle_user_consume_d[cancle_user_consume_d['t_gap']>=0]
# 现在cancle_user_consume_d包括了关注到取消关注的时间间隔，累计消费次数和人数，然后分别用时间间隔和累计消费次数来groupby以求出
# 不同间隔的人数，和各累计消费次数下的人数



# 算出不同间隔天数下的人数
cancle_re1=pd.pivot_table(cancle_user_consume_d,index='t_gap',values='number',aggfunc=np.sum)
cancle_re1=cancle_re1.reset_index()

# 写出这个cut函数花了很多时间，暴露出很大问题呀，大于180天以上的还没有标签，13个点需要12个标签
cut_points=[0,0.9,7,14,21,28,35,42,49,60,90,120,180]
labels=['0-当天','1-7天','8-14天','15-21天','22-28天','29-35天','36-42天','43-49天','50-60天','61-90天','91-120天','121-180天']
cancle_re1['interval']=cmycut(cancle_re1['t_gap'], cut_points, labels)
cancle_re1['interval']=cancle_re1['interval'].where(cancle_re1['interval'].notnull(),'180-天以上')
# 到此便得出了每一天所在的区间，然后在透视
cancle_re1_re=pd.pivot_table(cancle_re1,index='interval',values='number',aggfunc=np.sum)
cancle_re1_re=cancle_re1_re.reset_index()
cancle_re1_re['number'].fillna(0,inplace=True)
cancle_re1_re['占比']=cancle_re1_re['number']/cancle_re1_re['number'].sum()
# print(cancle_re1_re)
# cancle_re1_re.fillna(0,inplace=True)

# close()
cancle_data=[]
for a in cancle_re1_re['interval']:
    d=int(a.split('-')[0])
    cancle_data.append(d)
cancle_re1_re['interval_split']=cancle_data
cancle_re1_re_re2=cancle_re1_re.sort_values(by='interval_split')
cancle_re1_re_re2['new_index']=np.arange(len(cancle_re1_re_re2))
cancle_re1_re_re2=cancle_re1_re_re2.set_index('new_index')
cancle_re1_re_re2=cancle_re1_re_re2.reset_index()
cxuanf(3235, cancle_re1_re_re2['new_index'], cancle_re1_re_re2['interval'], cancle_re1_re_re2['number'],
       cancle_re1_re_re2['占比'], '不同时间段取关人数和占比', '取关人数', '取关人数占比')


# 算出取关前的累计消费次数
cancle_re2=pd.pivot_table(cancle_user_consume_d,index='total_consumes_num',values='number',aggfunc=np.sum)
cancle_re2=cancle_re2.reset_index()
# cut_points2=[0,0.9,1.9,2.9,3.9,10000]
# labels2=['0次','1次','2次','3次','4次及以上']
cut_points2=[0,0.9,1.9,10000]
labels2=['0次','1次','2次及以上']

cancle_re2['times']=cmycut(cancle_re2['total_consumes_num'],cut_points2,labels2)
cancle_re2_re=pd.pivot_table(cancle_re2,index='times',values='number',aggfunc=np.sum)
cancle_re2_re=cancle_re2_re.reset_index()
cancle_re2_re=cancle_re2_re[cancle_re2_re['number']>0]
# print(cancle_re2_re)
cbing1(3236, cancle_re2_re['number'],cancle_re2_re['times'], '取关前的累计消费次数')


# 11.会员的资料完善程度
# 没有取关资料的完善程度
info_makeup='''select date_format(u.uregistered, '%%Y%%m') '月份',
count(u.uid) '总人数', 
count(case when u.uGender=2 or u.ugender=1 then u.uid end) '性别完善人数',
count(case when datediff(curdate(),u.ubirthday)>=0 then u.uid end) '生日完善人数',
count(case when (u.uGender=2 or u.ugender=1) and datediff(curdate(),u.ubirthday)>=0 and u.uphone>0 and u.uname is not null then u.uid end) '全部资料完善人数',
count(case when u.uphone>0 then u.uid end) '手机号完善人数',
count(case when u.uname is not null then u.uid end) '姓名完善程人数',
concat(round(100*count(case when u.uname is not null then u.uid end)/count(u.uid),2),'%%') '姓名完善度',
concat(round(100*count(case when u.uphone>0 then u.uid end)/count(u.uid),2),'%%') '手机号完善度',
concat(round(100*count(case when u.uGender=2 or u.ugender=1 then u.uid end)/count(u.uid),2),'%%') '性别资料完善度',
concat(round(100*count(case when datediff(curdate(),u.ubirthday)>=0 then u.uid end)/count(u.uid),2),'%%') '生日资料完善度',
concat(round(100*count(case when (u.uGender=2 or u.ugender=1) and datediff(curdate(),u.ubirthday)>=0 and u.uphone>0 and u.uname is not null then u.uid end)/count(u.uid),2),'%%') '全部资料完善度'
from welife%s.welife_users%s u 
where u.uregistered>='%s' and u.uregistered < '%s' 
and u.bid=%i
and uCardStatus=2
group by date_format(u.uregistered, '%%Y%%m')''' %(p.dbs,p.tbs,p.ftime_s,p.ftime_e,p.bid)
print('11.未取关的资料完善')
info_makeup_d=wesql(info_makeup)
# 只选择全部资料完善程度
info_makeup_d_all=info_makeup_d[['月份','总人数','全部资料完善人数','手机号完善人数']]
info_makeup_d_all=info_makeup_d_all.copy()
info_makeup_d_all['all_rate']=info_makeup_d_all['全部资料完善人数']/info_makeup_d_all['总人数']
cline_h1(32316, info_makeup_d_all['月份'],info_makeup_d_all['all_rate'] , '未取关会员全部资料完善程度占比', 15)
# 西贝的全部资料完善的程度太低了，所以在拿出手机号出来看看
info_makeup_d_all['phone_rate']=info_makeup_d_all['手机号完善人数']/info_makeup_d_all['总人数']
cline_h1(32317, info_makeup_d_all['月份'],info_makeup_d_all['phone_rate'] , '未取关会员手机完善程度占比', 15)



# 取关的人的完善资料的程度
cancle_user_info_makeup='''select date_format(u.uregistered, '%%Y%%m') '月份',
count(u.uid) '总人数', 
count(case when u.uGender=2 or u.ugender=1 then u.uid end) '性别完善人数',
count(case when datediff(curdate(),u.ubirthday)>=0 then u.uid end) '生日完善人数',
count(case when (u.uGender=2 or u.ugender=1) and datediff(curdate(),u.ubirthday)>=0 and u.uphone>0 and u.uname is not null then u.uid end) '全部资料完善人数',
count(case when u.uphone>0 then u.uid end) '手机号完善人数',
count(case when u.uname is not null then u.uid end) '姓名完善程人数',
concat(round(100*count(case when u.uname is not null then u.uid end)/count(u.uid),2),'%%') '姓名完善度',
concat(round(100*count(case when u.uphone>0 then u.uid end)/count(u.uid),2),'%%') '手机号完善度',
concat(round(100*count(case when u.uGender=2 or u.ugender=1 then u.uid end)/count(u.uid),2),'%%') '性别资料完善度',
concat(round(100*count(case when datediff(curdate(),u.ubirthday)>=0 then u.uid end)/count(u.uid),2),'%%') '生日资料完善度',
concat(round(100*count(case when (u.uGender=2 or u.ugender=1) and datediff(curdate(),u.ubirthday)>=0 and u.uphone>0 and u.uname is not null then u.uid end)/count(u.uid),2),'%%') '全部资料完善度'
from welife%s.welife_users%s u 
where u.uregistered>='%s' and u.uregistered < '%s' 
and u.bid=%i and uCardStatus=3
group by date_format(u.uregistered, '%%Y%%m')''' %(p.dbs,p.tbs,p.ftime_s,p.ftime_e,p.bid)
print('11.2取消关注的人完善资料程度')
cancle_user_info_makeup=wesql(cancle_user_info_makeup)
cancle_user_info_makeup_all=cancle_user_info_makeup[['月份','总人数','全部资料完善人数','手机号完善人数']]
cancle_user_info_makeup_all=cancle_user_info_makeup_all.copy()
cancle_user_info_makeup_all['all_rate']=cancle_user_info_makeup_all['全部资料完善人数']/cancle_user_info_makeup_all['总人数']
cline_h1(32318, cancle_user_info_makeup_all['月份'],cancle_user_info_makeup_all['all_rate'] , '取关会员全部资料完善程度占比', 15)

cancle_user_info_makeup_all['phone_rate']=cancle_user_info_makeup_all['手机号完善人数']/cancle_user_info_makeup_all['总人数']
cline_h1(32319, cancle_user_info_makeup_all['月份'],cancle_user_info_makeup_all['phone_rate'] , '取关会员手机完善程度占比', 15)




# 消费会员的未消费会员的完善资料程度

# 消费会员资料的完善程度
consume_info_makeup='''select date_format(u.uregistered, '%%Y%%m') '月份',
count(u.uid) '总人数', 
count(case when u.uGender=2 or u.ugender=1 then u.uid end) '性别完善人数',
count(case when datediff(curdate(),u.ubirthday)>=0 then u.uid end) '生日完善人数',
count(case when (u.uGender=2 or u.ugender=1) and datediff(curdate(),u.ubirthday)>=0 and u.uphone>0 and u.uname is not null then u.uid end) '全部资料完善人数',
count(case when u.uphone>0 then u.uid end) '手机号完善人数',
count(case when u.uname is not null then u.uid end) '姓名完善程人数',
concat(round(100*count(case when u.uname is not null then u.uid end)/count(u.uid),2),'%%') '姓名完善度',
concat(round(100*count(case when u.uphone>0 then u.uid end)/count(u.uid),2),'%%') '手机号完善度',
concat(round(100*count(case when u.uGender=2 or u.ugender=1 then u.uid end)/count(u.uid),2),'%%') '性别资料完善度',
concat(round(100*count(case when datediff(curdate(),u.ubirthday)>=0 then u.uid end)/count(u.uid),2),'%%') '生日资料完善度',
concat(round(100*count(case when (u.uGender=2 or u.ugender=1) and datediff(curdate(),u.ubirthday)>=0 and u.uphone>0 and u.uname is not null then u.uid end)/count(u.uid),2),'%%') '全部资料完善度'
from welife%s.welife_users%s u 
where u.uregistered>='%s' and u.uregistered < '%s' 
and u.bid=%i
and uConsumeNum >0
group by date_format(u.uregistered, '%%Y%%m')''' %(p.dbs,p.tbs,p.ftime_s,p.ftime_e,p.bid)
print('13.有消费会员的资料完善')
consume_info_makeup_d=wesql(consume_info_makeup)
# 只选择全部资料完善程度
consume_info_makeup_d_all=consume_info_makeup_d[['月份','总人数','全部资料完善人数','手机号完善人数']]
consume_info_makeup_d_all=consume_info_makeup_d_all.copy()
consume_info_makeup_d_all['all_rate']=consume_info_makeup_d_all['全部资料完善人数']/consume_info_makeup_d_all['总人数']
cline_h1(323161, consume_info_makeup_d_all['月份'],consume_info_makeup_d_all['all_rate'] , '有消费会员全部资料完善程度占比', 13)
# 西贝的全部资料完善的程度太低了，所以在拿出手机号出来看看
consume_info_makeup_d_all['phone_rate']=consume_info_makeup_d_all['手机号完善人数']/consume_info_makeup_d_all['总人数']
cline_h1(323171, consume_info_makeup_d_all['月份'],consume_info_makeup_d_all['phone_rate'] , '有消费会员手机完善程度占比', 13)




# 未消费消费会员资料的完善程度
non_consume_info_makeup='''select date_format(u.uregistered, '%%Y%%m') '月份',
count(u.uid) '总人数', 
count(case when u.uGender=2 or u.ugender=1 then u.uid end) '性别完善人数',
count(case when datediff(curdate(),u.ubirthday)>=0 then u.uid end) '生日完善人数',
count(case when (u.uGender=2 or u.ugender=1) and datediff(curdate(),u.ubirthday)>=0 and u.uphone>0 and u.uname is not null then u.uid end) '全部资料完善人数',
count(case when u.uphone>0 then u.uid end) '手机号完善人数',
count(case when u.uname is not null then u.uid end) '姓名完善程人数',
concat(round(100*count(case when u.uname is not null then u.uid end)/count(u.uid),2),'%%') '姓名完善度',
concat(round(100*count(case when u.uphone>0 then u.uid end)/count(u.uid),2),'%%') '手机号完善度',
concat(round(100*count(case when u.uGender=2 or u.ugender=1 then u.uid end)/count(u.uid),2),'%%') '性别资料完善度',
concat(round(100*count(case when datediff(curdate(),u.ubirthday)>=0 then u.uid end)/count(u.uid),2),'%%') '生日资料完善度',
concat(round(100*count(case when (u.uGender=2 or u.ugender=1) and datediff(curdate(),u.ubirthday)>=0 and u.uphone>0 and u.uname is not null then u.uid end)/count(u.uid),2),'%%') '全部资料完善度'
from welife%s.welife_users%s u 
where u.uregistered>='%s' and u.uregistered < '%s' 
and u.bid=%i
and uConsumeNum <1
group by date_format(u.uregistered, '%%Y%%m')''' %(p.dbs,p.tbs,p.ftime_s,p.ftime_e,p.bid)
print('14.未消费会员的资料完善')
non_consume_info_makeup_d=wesql(non_consume_info_makeup)
# 只选择全部资料完善程度
non_consume_info_makeup_d_all=non_consume_info_makeup_d[['月份','总人数','全部资料完善人数','手机号完善人数']]
non_consume_info_makeup_d_all=non_consume_info_makeup_d_all.copy()
non_consume_info_makeup_d_all['all_rate']=non_consume_info_makeup_d_all['全部资料完善人数']/non_consume_info_makeup_d_all['总人数']
cline_h1(323162, non_consume_info_makeup_d_all['月份'],non_consume_info_makeup_d_all['all_rate'] , '未消费会员全部资料完善程度占比', 13)
# 西贝的全部资料完善的程度太低了，所以在拿出手机号出来看看
non_consume_info_makeup_d_all['phone_rate']=non_consume_info_makeup_d_all['手机号完善人数']/non_consume_info_makeup_d_all['总人数']
cline_h1(323172, non_consume_info_makeup_d_all['月份'],non_consume_info_makeup_d_all['phone_rate'] , '未消费会员手机完善程度占比', 13)


# 本来打算将两条线画在一个fig里面，但是又会有标签重叠的情况，所有作罢
# fig=plt.figure(323172,figsize=(10,6),dpi=200)
# plt.plot(non_consume_info_makeup_d_all['月份'],non_consume_info_makeup_d_all['all_rate'],'-o',non_consume_info_makeup_d_all['phone_rate'],'-o')
# plt.show()




# close()


