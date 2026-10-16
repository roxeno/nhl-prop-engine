weight = 0.2 #starting of season
# weight = 0.4 #middle of season
# weight = 0.8 #late of season

def blend_rate(current, career, weight):
    blended = weight * current + (1-weight) * career



#
#def opponent_factor(opp_rate, league_rate):
    #factor = opp_rate / league_rate

#def expected_lambda(rate_per_60, toi_min, opp_factor, home):
   # if (home == "home"):
   #     home_mult = 1.05
   #else:
   #     home_mult = 0.97

#lam = rate_per_60 * (toi_min / 60) * opp_factor * home_mult

#Poisson call
#full_distribution(λ, max_n)