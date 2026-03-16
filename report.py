import requests, xml.etree.ElementTree as ET, warnings, os
warnings.filterwarnings('ignore')
NS = 'http://tableau.com/api'
TABLEAU_SERVER = os.environ['TABLEAU_SERVER']
TABLEAU_SITE = os.environ['TABLEAU_SITE']
PAT_NAME = os.environ['TABLEAU_PAT_NAME']
PAT_SECRET = os.environ['TABLEAU_PAT_SECRET']
ANTHROPIC_KEY = os.environ['ANTHROPIC_API_KEY']
SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK_URL']
res = requests.post(f'{TABLEAU_SERVER}/api/3.21/auth/signin',json={'credentials':{'personalAccessTokenName':PAT_NAME,'personalAccessTokenSecret':PAT_SECRET,'site':{'contentUrl':TABLEAU_SITE}}})
root = ET.fromstring(res.text)
token = root.find(f'.//{{{NS}}}credentials').get('token')
site_id = root.find(f'.//{{{NS}}}site').get('id')
all_data = {}
for name,vid in {
    'Funnel CVR':'33a63b48-1ee4-4444-a37b-0bf58abb2e48',
    'Swimlane Funnel':'3b3ca450-34ad-495b-ad6a-af474a567151',
    'Category CTR':'e9683d3f-950f-4d1a-bfbb-db0fa5d7db09',
    '할인주문비중':'081db35d-3279-43df-83bf-d3835599d632',
    '할인금액비중':'96f4cc31-b5c5-41c2-9339-816cd90ee6d7',
    'Existing Customers':'bc36368d-12df-4433-8c50-f5f94f7d1bba'
}.items():
    r = requests.get(f'{TABLEAU_SERVER}/api/3.21/sites/{site_id}/views/{vid}/data',headers={'x-tableau-auth':token})
    all_data[name] = r.text[:800]
    print(f'{name} 수집 완료')
cr = requests.post('https://api.anthropic.com/v1/messages',headers={'x-api-key':ANTHROPIC_KEY,'anthropic-version':'2023-06-01','content-type':'application/json'},json={'model':'claude-sonnet-4-20250514','max_tokens':1500,'messages':[{'role':'user','content':f'''요기요 데이터를 분석해서 Slack 리포트를 작성해주세요.

[전환율 데이터]
Funnel CVR: {all_data["Funnel CVR"]}
Swimlane: {all_data["Swimlane Funnel"]}
Category CTR: {all_data["Category CTR"]}

[쿠폰/할인 데이터]
할인주문비중: {all_data["할인주문비중"]}
할인금액비중: {all_data["할인금액비중"]}
기존고객현황: {all_data["Existing Customers"]}

*📊 요기요 일일 리포트* 형식으로:
1. 전환율 핵심 수치
2. 쿠폰/할인 효과 분석
3. 이상 징후
4. 추천 액션 3가지
mrkdwn으로 작성'''}]})
report = cr.json()['content'][0]['text']
print('Claude 분석 완료')
sr = requests.post(SLACK_WEBHOOK,json={'text':report})
print('Slack 전송 완료!' if sr.status_code==200 else f'오류:{sr.text}')
