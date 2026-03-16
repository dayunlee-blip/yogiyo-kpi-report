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
for name,vid in {'Funnel CVR':'33a63b48-1ee4-4444-a37b-0bf58abb2e48','Swimlane Funnel':'3b3ca450-34ad-495b-ad6a-af474a567151','Category CTR':'e9683d3f-950f-4d1a-bfbb-db0fa5d7db09'}.items():
    r = requests.get(f'{TABLEAU_SERVER}/api/3.21/sites/{site_id}/views/{vid}/data',headers={'x-tableau-auth':token})
    all_data[name] = r.text[:800]
    print(f'{name} 수집 완료')
cr = requests.post('https://api.anthropic.com/v1/messages',headers={'x-api-key':ANTHROPIC_KEY,'anthropic-version':'2023-06-01','content-type':'application/json'},json={'model':'claude-sonnet-4-20250514','max_tokens':1000,'messages':[{'role':'user','content':f'요기요 전환율 데이터 분석 Slack 리포트:\nFunnel CVR:{all_data["Funnel CVR"]}\nSwimlane:{all_data["Swimlane Funnel"]}\nCTR:{all_data["Category CTR"]}\n\n*📊 요기요 일일 전환율 리포트* 형식으로 핵심수치/이상징후/추천액션3가지 mrkdwn'}]})
report = cr.json()['content'][0]['text']
print('Claude 분석 완료')
sr = requests.post(SLACK_WEBHOOK,json={'text':report})
print('Slack 전송 완료!' if sr.status_code==200 else f'오류:{sr.text}')
