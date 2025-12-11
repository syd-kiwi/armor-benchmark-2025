from openai import OpenAI
client = OpenAI()

models = client.models.list()
for m in models.data:
    print(m.id)
