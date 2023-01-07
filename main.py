import streamlit as st
from io import StringIO
import pandas as pd
import plotly_express as px
st.markdown("# WhatsApp Chat Analyzer")
st.markdown("##### Analyze your chat with others on WhatsApp, know which one of you is **`رغاى`** 😂 ")
# sidebar
st.sidebar.markdown("""
# Options
### Follow the follwing steps
1) Open the individual chat `Individual or Group`.
2) Tap options > More > Export chat.
3) Choose export without media.
 هيقوم فاتحلك اختيارات كده ف الافضل ارفعه درايف وحمله ع الموقع بعدها😃
""")

chat_type =st.sidebar.selectbox("Chat Type",["Group Chat" , "Individual Chat"])
file = st.sidebar.file_uploader("The file",type="txt")
st.sidebar.markdown("متخفش وربنا مفيش حد هيشوف الداتا 😂 ")
# start working with the file
# convert and get the final data
#----------------------------------helper functions --------------------------------
@st.cache
def parse_date(data : pd.DatetimeIndex):
    """
    takes the data column as string and return the column clean
    """
    # split the column according to the /
    d = data.str.split("/",expand=True)
    d[0] =d[0].astype(int)
    d[1] = d[1].astype(int)
    # get the day column
    if d[0].max() >12:
        d["day"] = d[0]
        d["month"] = d[1]
    else:
        d["month"] = d[0]
        d["day"] = d[1]
    # process the year
    if len(d[2].iloc[2]) == 2:
        d["year"] = "20"+d[2]
    else:
        d["year"] = d[2]
    d["date"] = d["day"].astype(str)+"/" + d["month"].astype(str) +"/"+ d["year"]
    return d["date"]

def get_final_group(df,month):
    d = df[df["date"].dt.month == month]
    dates = d["date"].unique()
    d = d.groupby([d["date"],d["sender"]])["sender"].count().to_frame()
    senders = list(df.sender.unique())
    from collections import defaultdict
    sender_messages = defaultdict(list)
    for date in dates:
        if len(d.loc[date].index) == len(senders):
            for i ,sender in enumerate(senders):
                sender_messages[sender].append(d.loc[date].loc[sender].values[0])
        else :
            # get the sender :
            senders_less = d.loc[date].index
            # apped the data for the senders
            for i ,sender in enumerate(senders_less):
                sender_messages[sender].append(d.loc[date].loc[sender].values[0])
            # apped zeros for the rest
            rest = set(senders) - set(senders_less)
            for i ,sender in enumerate(rest):
                sender_messages[sender].append(0)
    ms = pd.DataFrame(sender_messages)
    ms["date"]=dates
    final = ms.melt(id_vars=["date"],value_vars=senders)
    return final
#-----------------------------------------------------------------------------------
@st.cache
def get_data(file_name,chat_type):
    stringio = StringIO(file_name.getvalue().decode("utf-8"))
    lines = stringio.readlines()
    #check the chat type
    if chat_type == "Group Chat":
        lines = lines[3:]
    else:
        lines = lines[1:]
    #choose only the linse that start with the dataes
    lines = ( line for line in lines )
    chat_lines = []
    for l in lines:
        if len(l) >10 :
            if (l[0].isdigit()) & ( "/" in l[0:10]):
                chat_lines.append((l))
    df = pd.Series(chat_lines).str.split("-",expand=True).iloc[:,0:2]
    df[["sender","message"]] = df[1].str.split(":",expand=True).iloc[:,0:2]
    df.drop([1],axis=1,inplace=True)
    df.columns = ["date","sender","message"]
    df[["date","hour"]] = df["date"].str.split(",",expand=True).iloc[:,0:2]
    df = df.dropna()
    df["date"] = parse_date(df["date"])
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
    def fucn(s):
        return s.strip().split(":")[0]+ " "+ s.strip().split(" ")[-1]
    df["hour"] = df["hour"].apply(fucn)
    # removed the unwanted chats
    if chat_type == "Group Chat":
        df = df.drop(df[df.sender.str.contains("added | removed")].index)
    return df

# try:
if file :
    # read the data and show a sample
    df = get_data(file,chat_type)
    st.write("**Sample data** from the chat")
    st.write(df.head())
    # columns with the messages from each user and the total messages
    senders = (df.sender.value_counts()).index
    messages = list((df.sender.value_counts()).values)
    total_messages = len(df)
    st.metric("Total Messages",total_messages, delta_color="inverse")
    # col_list = st.columns(len(senders)+1)
    # with col_list[0]:
    #     st.metric("Total Messages",total_messages)
    # for i, col in enumerate(col_list[1:]):
    #     with col:
    #         st.metric(str(senders[i]), messages[i])

    st.write("### Which one how send more message ?")
    b = df["sender"].value_counts()
    # draw a pie plot for the users count of message
    fig = px.pie(names=b.index, values=b.values,labels ={"names":"sender ","values":"num of messages "},)
    fig.update_traces(textposition='inside', textinfo='percent+label'
                        , hoverinfo='percent+label', marker=dict(line=dict(color='#000000', width=2)))
    fig.update_layout(
        title_text="Sender & Num of Messages ", legend_title_text="Sender",
        title_x=.5,showlegend=False,margin={"l":0,"r":0})
    st.plotly_chart(fig, use_container_width=True)
    st.write("### Which hour most chats happen at ?")
    h = df["hour"].value_counts().to_frame()
    h["text"] = h["hour"].astype(str)
    fig = px.bar(data_frame=h,x=h.index,y= "hour",labels={"index":"Hour ","hour":"","text":"messages "},text="text" ,title="Messages in each Hour")
    fig.update_traces(textposition='inside')
    fig.update_yaxes(showgrid=False,visible=False)
    fig.update_layout(title_x=.5,margin={"l":0,"r":0})
    st.plotly_chart(fig, use_container_width=True)

    # -------------------- the month question -------------------------------
    st.write("### What month most chats happen at ?")
    m = df.groupby(df["date"].dt.month)["sender"].count().to_frame()
    m["text"] = m["sender"].astype(str)
    fig = px.bar(data_frame=m, x=m.index, y="sender",  text="text",
                 labels={"date": "Month ", "sender": "", "text": "messages "},
                 title="Messages in each Month")
    fig.update_traces(textposition='inside')
    fig.update_yaxes(showgrid=False,visible=False)
    fig.update_layout(title_x=.5,margin={"l":0,"r":0})
    st.plotly_chart(fig, use_container_width=True)
    if st.checkbox("Analyze number of messages through a month ?"):
        month = st.selectbox("Choose the Month",df.date.dt.month.unique())
        c = st.checkbox("Show messages by each user ?")
        d = df[df["date"].dt.month ==  month]
        d = d.groupby(d["date"])["sender"].count()
        if not c:
            fig = px.line(x=d.index, y=d.values,title=f"Messages in each day in month { month}",labels={"x":"Date","y":"","text":"messages "})
        if c :
            # prepare the data
            # if chat_type == "Group Chat":
            #     final =  get_final_group(df,month)
            # else:
            final =  get_final_group(df,month)
            fig = px.line(data_frame=final, x="date",y="value",color="variable", title=f"Messages in each day in month {month} for each sender",
                          labels={"x": "Date", "value": ""})
        fig.update_layout(title_x=.5,legend_title_text="",legend_orientation="h",legend_y=-.2,legend_x=.3,legend_font_size=10,margin={"l":0,"r":0})
        st.plotly_chart(fig, use_container_width=True)
    st.info("Made With love ❤ Ahmed Elsayed")
# except:
#     st.error("There is error happened please inform me and make sure you choose the right options")