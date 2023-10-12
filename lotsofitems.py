from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///itemcatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# session.delete(Item)
# session.commit()
# session.delete(Category)
# session.commit()

# Create dummy user
User1 = User(name="Chandru Mg", email="chandru_mg@infy.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()
# print((datetime.now() - timedelta(seconds=160)).strftime("%Y-%m-%d %H:%M:%S"))
# category - Soccer
category = Category(name="Soccer")

session.add(category)
session.commit()

item1 = Item(user_id=1, title="Soccer Jersey", description="This is Soccer Jersey",
added_date_time=(datetime.now() + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S"),category=category)

session.add(item1)
session.commit()


item2 = Item(user_id=1, title="Soccer Shoe", description=" This is Soccer Shoe",
added_date_time=(datetime.now() + timedelta(seconds=2)).strftime("%Y-%m-%d %H:%M:%S"),category=category)

session.add(item2)
session.commit()


item3 = Item(user_id=1, title="Soccer Ball", description="This is Soccer Ball",
added_date_time=(datetime.now() + timedelta(seconds=3)).strftime("%Y-%m-%d %H:%M:%S"),category=category)

session.add(item3)
session.commit()

item4 = Item(user_id=1, title="Soccer Goggles", description=" This is Soccer Goggles",
added_date_time=(datetime.now() + timedelta(seconds=4)).strftime("%Y-%m-%d %H:%M:%S"),category=category)

session.add(item4)
session.commit()


# Category2 - Hockey

category = Category(name="Hockey")

session.add(category)
session.commit()

item1 = Item(user_id=1, title="Hockey Ball", description="This is Hockey Ball",
added_date_time=(datetime.now() + timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S"),category=category)

session.add(item1)
session.commit()


item2 = Item(user_id=1, title="Hockey Stick", description="This is Hockey Stick",
added_date_time=(datetime.now() + timedelta(seconds=6)).strftime("%Y-%m-%d %H:%M:%S"),category=category)

session.add(item2)
session.commit()


# Category3
category = Category(name="Cricket")

session.add(category)
session.commit()

item1 = Item(user_id=1, title="Cricket Helmet", description="This is Cricket Helmet",
added_date_time=(datetime.now() + timedelta(seconds=7)).strftime("%Y-%m-%d %H:%M:%S"),category=category)

session.add(item1)
session.commit()


item2 = Item(user_id=1, title="Cricket Bat", description="This is Cricket Bat",
added_date_time=(datetime.now() + timedelta(seconds=8)).strftime("%Y-%m-%d %H:%M:%S"),category=category)

session.add(item2)
session.commit()


item3 = Item(user_id=1, title="Cricket Ball", description="This is Cricket Ball",
added_date_time=(datetime.now() + timedelta(seconds=9)).strftime("%Y-%m-%d %H:%M:%S"),category=category)

session.add(item3)
session.commit()

print("added menu items!")
