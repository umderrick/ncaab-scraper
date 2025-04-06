import os

dir_name = "C:/Users/umder/Desktop/Personal/CBBScraper"
test = os.listdir(dir_name)

for item in test:
    if item.endswith(".json"):
        os.remove(os.path.join(dir_name, item))

for item in test:
    if item.endswith(".txt"):
        os.remove(os.path.join(dir_name, item))

for item in test:
    if item.endswith(".md"):
        os.remove(os.path.join(dir_name, item))

for item in test:
    if item.endswith(".html"):
        os.remove(os.path.join(dir_name, item))
        