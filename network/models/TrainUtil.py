import torch
import os

def train_simple_conv(model, cfg, train_loader, optimizer, epoch):
    # 重要！pytorch的接口函数，将网络设置为训练模式，它会对dropout，BN等模块有影响
    # 因为司机网络中调用的ResNet正好有BN层
    model.train()
    total_loss = 0

    print (len(optimizer.param_groups))
    for batch_idx, sampled_batch in enumerate(train_loader):

        # 梯度清零
        optimizer.zero_grad()
        # 使用模型计算输出
        nn_outputs = model(sampled_batch['data'].to(cfg.device))
        # 使用输出和真值计算损失
        loss = model.compute_loss(nn_outputs,sampled_batch, cfg)

        # 计算损失对参数的梯度
        loss.backward()
        # 执行一次优化
        optimizer.step()

        # 计算每个batch的loss叠加起来的总损失
        total_loss += loss
        # 每隔100次保存一次模型参数及训练的结果  并没有在tensorboard进行显示
        if batch_idx % cfg.log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * cfg.batch_size, len(train_loader.dataset),
                100. * batch_idx / len(train_loader), loss.item()))
            torch.save(model.state_dict(), os.path.join(cfg.checkpoints_path,"ChauffeurNet_{}_{}.pt".format(epoch,batch_idx)))

    # 计算每个batch平均的loss
    total_loss /= len(train_loader)
    # ？
    cfg.scheduler.step(total_loss)
    for param_group in optimizer.param_groups:
        print(param_group['lr'])
    del total_loss

