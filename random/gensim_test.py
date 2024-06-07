import gensim.downloader

model = gensim.downloader.load(name="glove-wiki-gigaword-50")
result = model.most_similar(positive=["sushi", "italy"], negative=["japan"])
print(result)

# man - king = woman - queen
# man - king - woman = - queen
# - man + king + woman = queen

# japan - sushi = germany - x
# japan - sushi - german = - x
# - japan + sushi + germany = x
