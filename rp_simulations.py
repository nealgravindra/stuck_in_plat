import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind

def rp(place, num_fights, ranked_level='plat'):
    # assume even split between squad
    cost = {'bronze':0, 'silver':12,
            'gold':24, 'plat':36,
            'diamond':48, 'master':60,
            'pred':60}
    cost = cost[ranked_level]
    ranked_s7 = {i:(0, 10) for i in range(1, 21)}
    ranked_s7[1] = (100, 25)
    ranked_s7[2] = (60, 20)
    ranked_s7[3] = (40, 20)
    ranked_s7[4] = (40, 15)
    ranked_s7[5] = (30, 15)
    ranked_s7[6] = (30, 12)
    ranked_s7[7] = (20, 12)
    ranked_s7[8] = (20, 12)
    ranked_s7[9] = (10, 12)
    ranked_s7[10] = (10, 12)
    points = ranked_s7[place][0] + ranked_s7[place][1]*num_fights*(1/3) - cost
    return place, num_fights, points

def play_game(place, num_fights, topn=np.inf, p_winfight=0.5, p_getaway=0.67):
    '''
    Set topn=np.inf to always fight or topn=2 to be rat
    '''
    start = place
    p_fight =  1/(place-1)

    if np.random.rand(1)>p_fight:
        # you didn't have to fight
        place = place - 1

    else:
        if place <= topn:
            # fight!
            if np.random.rand(1)<np.random.normal(loc=p_winfight, scale=0.25):
                num_fights = num_fights + 1
                place = place - 1
        else:
            # run!
            if np.random.rand(1) < np.random.normal(loc=p_getaway, scale=0.1):
                place = place - 1

    if start == place or place==1:
        return place, num_fights
    else:
        return play_game(place, num_fights, topn=topn)

def sim_topn(n_games=10, n_sample=100, n_polulation=10000, topn=np.inf, savefigs=False):
    # population
    data_population = pd.DataFrame()
    for i in range(n_polulation):
        place, num_fights, points = rp(*play_game(20, 0, topn=topn), ranked_level='plat')
        dt = pd.DataFrame({'Place':place,
                           'n_fights':num_fights,
                           'RP':points}, index=[0])
        data_population = data_population.append(dt, ignore_index=True)

    # randomly sample
    if n_sample==None:
        results = data_population
        n_games=1
    else:
        results = pd.DataFrame()
        for i in range(n_sample):
            dt = data_population.sample(n=n_games, replace=True)
            results = results.append(pd.DataFrame({'Place':dt['Place'].mean(),
                                                   'n_fights':dt['n_fights'].mean(),
                                                   'RP':dt['RP'].sum()}, index=[0]))

    # plot
    fig, ax = plt.subplots(1,3, figsize=(11,2))
    sns.distplot(results['Place'], ax=ax[0], color=sns.cubehelix_palette(3)[0])
    sns.distplot(results['RP'], ax=ax[1], color=sns.cubehelix_palette(3)[1])
    sns.distplot(results['n_fights'], ax=ax[2], color=sns.cubehelix_palette(3)[2])
    ax[0].set_xlim([0,20])
    ax[0].set_xlabel('Placement per match\n(session ave.)')
    ax[1].set_xlabel('Summed RP during session')
    ax[2].set_xlabel('Number of fights won\nper match (session ave.)')
    fig.suptitle('Aggregate over {} games played in a session, fight if top {}'.format(n_games, topn))

    if savefigs:
        fig.savefig('default_sim.pdf')
        results.to_csv('default_sim.csv')

    return results

def experiments(strategy='default'):
    if strategy=='default':
        results = sim_topn()
    elif strategy=='top7':
        results = sim_topn(topn=7)
    return results

if __name__ == '__main__':

    results_default = experiments()
    results_top7 = experiments(strategy='top7')

    print('Diff. in means (default - top7): {:.2f} (P={:.3f})'.format(
      results_default['RP'].mean() - results_top7['RP'].mean(),
      ttest_ind(results_default['RP'], results_top7['RP'], equal_var=False)[1]))
