#-*- coding:utf-8 -*-
#"2018年1月6日"

import matplotlib.pyplot as plt 
from  datetime import datetime
import numpy as np
import pandas as pd


# 在method里面添加了plt.hold(),这是以前的


# 添加标签，百分号分割
def autolabel(x,y,size):
    for a,b in zip(x,y):
        plt.text(a,b,"{:,}".format(int(b)),ha='center',va='bottom',fontsize=size)

# 添加标签，百分号分割,上面的不能指定字体的大小，有时候要用到，但是不想在autolabel上修改，所以新建了一个
def autolabel_size(x,y,size):
    for a,b in zip(x,y):
        plt.text(a,b,"{:,}".format(int(b)),ha='center',va='bottom',fontsize=size)




        
# 添加标签，保留两位小数(对于小于1的地方用百分号，大于1的地方用小数)
def autolabel2(x,y,size):
    for a,b in zip(x,y):
        if y.mean()>1:
            plt.text(a,b,'%.2f' %b,ha='center',va='bottom',fontsize=size)
        else:
            plt.text(a,b,'%.2f%%' %(b*100),ha='center',va='bottom',fontsize=size)
        
        
# bar:横轴是月份，纵轴是数量，n表示第几张fig,t是图片的title
def bar_h(n,x,y,t):
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    plt.bar(x,y) 
    autolabel(x,y,13) 
    plt.title(t)  
    plt.xticks(x,x,rotation=30)
    plt.savefig('%i%s'%(n,t))  
 
 # bar保留两位小数:横轴是月份，纵轴是数量，n表示第几张fig,t是图片的title
def bar_h2(n,x,y,t):
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    plt.bar(x,y) 
    autolabel2(x,y,12) 
    plt.title(t)  
    plt.savefig('%i%s'%(n,t))  
    
# 上面的bar只能画横轴是月份的，现在改成其他的分类变量,而且是barh
def bar_h3(n,x,x_change,y,t):
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    plt.barh(x,y)
    if y.mean()>10:
        for a,b in zip(x,y):
            plt.text(a,b,"{:,}".format(int(b)),ha='center',va='bottom',fontsize=5)
    else:
        for a,b in zip(x,y):
            plt.text(b,a,'%.2f%%'%(b*100),ha='left',va='bottom',fontsize=15)
    plt.yticks(x,x_change,fontsize='small')
    plt.xticks(())
    plt.title(t)
    plt.savefig('%i%s'%(n,t))  

# line:在一张fig里面画出两条线,t1,t2分别是格式的label,l1,l2是两条线的label
def line_h(n,x,y1,y2,l1,l2,t):
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    plt.plot(x,y1,'-o',label=l1)
    plt.plot(x,y2,'-o',label=l2)
    plt.legend()
    autolabel(x,y1,13)
    autolabel(x,y2,13)
    plt.title(t)
    plt.savefig('%i%s+%s'%(n,l1,l2))

# 旋风图，一柱一线,先画柱子，后画线条,bar是数值，line 是小数
# 需要双坐标轴，l1指的是线的label,t是图片title,有时候x横坐标可能不是我们想要的标签，所以替换成x_change
def xuanf(n,x,x_change,y2,y1,title,legend1,legend2):
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    ax1=fig.add_subplot(111)
    bar_p=ax1.bar(x,y2)
    for a,b in zip(x,y2):
        if a%2!=0:
            plt.text(a,b,'{:,}'.format(b),ha='center',va='bottom',fontsize=13)
#     autolabel(x,y2,13)
    ax2=ax1.twinx()
    line_p,=ax2.plot(x,y1,'r-o')
    for a,b in zip(x,y1):
        if y1.mean()<1:
            plt.text(a,b,'%.0f%%'%(b*100),ha='center',va='bottom',fontsize=13)
        else:
            plt.text(a,b,'%.2f'%b,ha='center',va='bottom',fontsize=13)

#     autolabel2(x,y1,13)
    plt.title(title)
    plt.legend([bar_p,line_p],['%s' %legend1,'%s' %legend2],loc=3,bbox_to_anchor=[0,1],fontsize='small')
    plt.xticks(x,x_change,rotation=45)
    plt.savefig('%i%s'%(n,title))


# 计算消费周期的时候，实不加数字标签上去，所以只好再写一个xuanf
def xuanf1(n,x,y2,y1,title,legend1,legend2,a):
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    ax1=fig.add_subplot(111)
    bar_p=ax1.bar(x,y2)
    plt.annotate('消费周期:%s天' %int(round(a,0)),xy=(x.mean(),y2.mean()+100))
    ax2=ax1.twinx()
    line_p,=ax2.plot(x,y1,'r')
    ax2.scatter(44,0.6,s=25,color='b')
#     这个标签始终加的很乱，先放这儿
#     myla=np.arange(0,x.count(),50)
#     plt.xticks(x,myla,size='small',rotation=90)
    
    plt.title(title)
    plt.legend([bar_p,line_p],['%s' %legend1,'%s' %legend2],loc=3,bbox_to_anchor=[0,1],fontsize='small')
    plt.savefig('%i%s'%(n,title))




# 两个柱子的旋风图，一个是数量，一个是百分比,或者两者之间相差了好几个数量级
# size表示两个变量之间相差的量级，legend1和legend2分别是两个柱子的名称
def xuanf2(n,x,y1,y2,size,title,legend1,legend2):
    fig=plt.figure(n,figsize=(10,7),dpi=200)
    xr=np.arange(len(x))
    plt.barh(xr,y1)
    for a,b in zip(xr,y1):
        plt.text(b,a,"{:,}".format(int(b)),ha='left',va='center',fontsize=15)
#     由于是水平的旋风图，所以y1是正的，y2是负的
    plt.barh(xr,-y2*size)
    if y2.mean()>10:
        for a,b in zip(xr,y2):
            plt.text(-b*size,a,"{:,}".format(int(b)),ha='right',va='center',fontsize=15)
    else:
        for a,b in zip(xr,y2):
            plt.text(-b*size,a,'%.2f' %b,ha='right',va='center',fontsize=15)
            
    plt.xticks(())
    plt.yticks(xr,x,fontsize='small',rotation=30)
    plt.title(title)
    plt.legend([legend1,legend2],loc=3,bbox_to_anchor=[0,1])
    
    plt.savefig('%i%s'%(n,title))




# 每次总要计算两个时间之间的间隔，直接写成函数调用,有时候可以有sid,有时候没有，所以做成可变的参数
# df是需要修改的数据框，col是sql取出来的时间，mean_value是判断流逝的时间节点，uid用来计算人数，
def to_days(df,col,mean_value,*sid):
#     先添加今天的时间，然后np.where判断状态，接着透视表，最后reset.index()
    df['todays']=datetime.now().strftime("%Y%m%d")
    col=col.apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
    df['todays']=df['todays'].apply(lambda x:datetime.strptime(str(x),"%Y%m%d"))
    df['interval']=df['todays']-col
    df['days']=df['interval'].apply(lambda x:x.days)
#     np.where判定状态,而且只做一次判断
    mean_value=int(mean_value)
    df['status']=np.where(df['days']>3*mean_value,'沉睡会员','非沉睡会员')

    return df

# 画矩阵图
# label是点的名称，x_label是x轴的标签，y_label是y轴的标签，title是图片的名称
def juz(n,x,y,label,x_label,y_label,title):
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    plt.scatter(x,y)
#     添加散点的标签
    for lab,a,b in zip(label,x,y):
        plt.text(a,b+1,lab,ha='center',va='bottom',size='x-small',rotation=45)
    
#     添加水平和竖直的平均值线
    plt.hlines(y=y.mean(),xmin=x.min(),xmax=x.max())
    plt.vlines(x=x.mean(),ymin=y.min(),ymax=y.max())
    
#     在水平和竖直的线上添加标签
    plt.text(x.max(),y.mean(),x_label,color='dodgerblue')
    plt.text(x.mean(),y.max(),y_label,color='dodgerblue')
    plt.title(title)
#     plt.xticks(())
#     plt.yticks(())
    plt.savefig('%i%s'%(n,title))


# 画饼图
def bing(n,x,y,title):
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    plt.pie(x,labels=y,autopct='%1.1f%%')
    plt.axis('equal')
    plt.title(title)
    plt.savefig('%i%s'%(n,title))
    
   

# 这个color是从public里面复制过来的 
color_sequence = ['#1f77b4', '#aec7e8', '#ff7f0e',
                '#ffbb78', '#2ca02c',
                '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5',
                '#8c564b', '#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f',
                '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5']


# 画出多条直线,df是将怎样数据框传进来
def double_line(n,x,df,xlab,ylab,alist,size,title):
    
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    ax=fig.add_subplot(111,frameon=False)
        # 设置y轴格式
    # plt.yticks(range(0, 1, 10), fontsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter('{:.0f}%'.format))
    # ax.set_ylim(0,2)
    plt.grid(True, 'major', 'y', ls='--', lw=.5, c='k', alpha=.3)
    plt.tick_params(axis='both', which='both', bottom='off', top='off',
                labelbottom='on', left='off', right='off', labelleft='on')

    for i,j in enumerate(alist):
        line=ax.plot(x,df[j],color=color_sequence[i])
#         获取每一列的最后一个值y_pos=df[j].iloc[-1]，用来text每条线的标签
        if i%2==0:
            plt.text(x.iloc[-1],df[j].iloc[-1],j,color=color_sequence[i],fontsize=size)
        else:  #偶数的时候，将text标在倒数第三个值处
            plt.text(x.iloc[-3],df[j].iloc[-3],j,color=color_sequence[i],fontsize=size)
    for i in ax.yaxis.get_major_ticks():
        i.label1On=False
        i.label2On=True
    ax.set_xlabel(xlab)
    ax.set_ylabel(ylab)
    ax.set_title(title)
    plt.savefig('%s%s'%(n,title))



# 分三档用来格式化，坐标轴的标签
def my_format(x,pos):
    if x>1e6:
        s='{:1.2f}百万'.format(x*1e-6)
    elif  x>1e4 and x<1e6:
        s='{:1.2f}万'.format(x*1e-4)
    else:
        s='{:1.2f}千'.format(x*1e-3)
    return s

# double在线条很多的时候可以用，如果线条较少的话，可以简单一些
# 比double_line更简单的double_line2用来画比如各等级每月消费金额，各等级每月新增
# df是二维数据结构，alist是数据框里面的会员等级
def double_line2(n,x,df,x_lab,y_lab,alist,title):
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    ax=fig.add_subplot(111)
    plt.grid(True, 'major', 'y', ls='--', lw=.5, c='k', alpha=.3)
    plt.tick_params(axis='both', which='both', bottom='off', top='off',
                labelbottom='on', left='off', right='off', labelleft='on')
    for i in alist:
        ax.plot(x,df[i],'-o')
#         autolabel_size(x,df[i],10)
    ax.set_xlabel(x_lab);ax.set_ylabel(y_lab);ax.set_title(title)
#     设置坐标轴显示格式
    ax.yaxis.set_major_formatter(plt.FuncFormatter(my_format))
#     x轴的坐标旋转一下
    my_xlabels=ax.get_xticklabels()
    plt.setp(my_xlabels,rotation=15,fontsize=10)
    
    for i in ax.yaxis.get_major_ticks():
        i.label1On=False
        i.label2On=True
    plt.legend()
    
    plt.savefig('%s%s'%(n,title))



# 画出多条直线,df是将怎样数据框传进来,和上面的double_line的区别是更改了Y轴的format
def double_line_format(n,x,df,xlab,ylab,alist,size,title):
    
    fig=plt.figure(n,figsize=(10,6),dpi=200)
    ax=fig.add_subplot(111,frameon=False)
        # 设置y轴格式
    # plt.yticks(range(0, 1, 10), fontsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(my_format))
    # ax.set_ylim(0,2)
    plt.grid(True, 'major', 'y', ls='--', lw=.5, c='k', alpha=.3)
    plt.tick_params(axis='both', which='both', bottom='off', top='off',
                labelbottom='on', left='off', right='off', labelleft='on')

    for i,j in enumerate(alist):
        line=ax.plot(x,df[j],color=color_sequence[i])
#         获取每一列的最后一个值y_pos=df[j].iloc[-1]，用来text每条线的标签
        if i%2==0:
            plt.text(x.iloc[-1],df[j].iloc[-1],j,color=color_sequence[i],fontsize=size)
        else:  #偶数的时候，将text标在倒数第三个值处
            plt.text(x.iloc[-3],df[j].iloc[-3],j,color=color_sequence[i],fontsize=size)
    for i in ax.yaxis.get_major_ticks():
        i.label1On=False
        i.label2On=True
    ax.set_xlabel(xlab)
    ax.set_ylabel(ylab)
    ax.set_title(title)
    plt.savefig('%s%s'%(n,title))








