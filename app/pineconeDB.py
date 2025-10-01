from pinecone import Pinecone
import os

pc = Pinecone(api_key="pcsk_6WvWws_9ibWmA81ab7QEN65iWvHHSMo231Bg8zoacEw1feaJh75mmUMBtEoCsdyL9BYuXN")

index = pc.Index("minnewyork")

stats = index.describe_index_stats()
print(stats)
