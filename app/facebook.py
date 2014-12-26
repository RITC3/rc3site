import facebook
from config import FACEBOOK_TOKEN
from decorators import async

@async
def send_async_fbpost(msg):
    pass
"""
def send_fbpost(subject, recipients, text_body, html_body):
    sender = BASE_ADMINS[0]
    msg = Message(subject, sender = sender, recipients = recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(msg)
"""

def rc3_post():
    token = 'CAAD4psDZByDkBAIrw39E1jFrZBdbRU6OyZAjiWKbhd0SEq31YJaZAPT3pog0dlg6QnaDx26VjCjlUJ4cKRKjehYkTvO6OLENlZA9k7h0gG57FpHgvrp0ZCP9ZAVa3atdOrPFujgIRZCAnq8ZAEeoJRMZCF665n3Xpd48L7bFUeaQ05ZCtHVVEKcIlhvcwPAZC8cn4VRrkEJ8O8kYy7MFalNZB9jZBCd1ZAnjMeRv6UZD'
    graph = facebook.GraphAPI(token)#FACEBOOK_TOKEN)
    profile = graph.get_object("me/groups")
    group_id = groups['data'][0]['id']
    return group_id
