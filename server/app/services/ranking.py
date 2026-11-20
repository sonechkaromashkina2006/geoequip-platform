def suitability(sim, acc, cost, acc_target, cost_target,
                w_sim=0.4, w_acc=0.3, w_cost=0.3):
    # sim: 0..1 (score из Neo4j)
    # acc, cost: 0..100 из БД -> разделить на 100
    # acc_target, cost_target: 0..1 (ползунки, Qt уже шлёт value/100)
    return w_sim*sim + w_acc*(1-abs(acc/100-acc_target)) + w_cost*(1-abs(cost/100-cost_target))