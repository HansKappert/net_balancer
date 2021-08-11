from model import model
from persistence import persistence
db = persistence()
m = model(db)
m.surplus = 3
print (m.surplus)
m.surplus = 4
print (m.surplus)