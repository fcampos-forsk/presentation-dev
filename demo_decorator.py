from profileit import profileit
from demo import generer_transactions

my_profile = profileit(generer_transactions)

my_profile(6000)