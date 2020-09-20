%% vnc t1 motor neuron similarity matrix PRIMARY NEURITES only
% starting with csv export of CATMAID neuron similarity results gives NBLAST scores as a
% matrix with skeleton ID headers. This matrix has left, right ("flipped" mixed). 
% Scores and header separated
load('lrT1primNblast88.mat');

% JMS's pymaid script was used to get names, bundles corresponding to these skeleton IDs in the
% transformed into template project
load('lrT1primNblast88Names.mat');
load('lrT1primNblast88LUT.mat');

%% left or right T1mns, broken up by nerve

% Hierarchical clustering with single linkage was performed on similarity 
% scores for motor neurons of each peripheral nerve using the SciPy Python 
% package by JMS

% ln: main leg nerve, an: accessory leg nerve, vn: ventral nerve, dn: dorsal nerve
nerve = 'an'; %choose ln, an, vn, or dn
side = 'left'; %chose left or right

if strcmp(side, 'left')
    if strcmp(nerve, 'ln')
        load('ln_lsingleHcT1primOrder.mat')
        hcOrder = ln_lsingleHcT1primOrder';
        nnames = ln_lsingleHcT1primOrder';
        plot_title = 'left T1 leg nerve MN clusters (by primary neurite; single linkage)';
    elseif strcmp(nerve, 'an')
        load('an_lsingleHcT1primOrder.mat')
        hcOrder = an_lsingleHcT1primOrder';
        nnames = an_lsingleHcT1primOrder';
        plot_title = 'left T1 accessory leg nerve MN clusters (by primary neurite; single linkage)';
    elseif strcmp(nerve, 'vn')
        load('vn_lsingleHcT1primOrder.mat')
        hcOrder = vn_lsingleHcT1primOrder';
        nnames = vn_lsingleHcT1primOrder';
        plot_title = 'left T1 ventral nerve MN clusters (by primary neurite; single linkage)';
    elseif strcmp(nerve, 'dn')
        load('dn_lsingleHcT1primOrder.mat')
        hcOrder = dn_lsingleHcT1primOrder';
        nnames = dn_lsingleHcT1primOrder';
        plot_title = 'left T1 dorsal nerve MN clusters (by primary neurite; single linkage)';
    end
elseif strcmp(side, 'right')
    if strcmp(nerve, 'ln')
        load('ln_rsingleHcT1primOrder.mat')
        hcOrder = ln_rsingleHcT1primOrder';
        nnames = ln_rsingleHcT1primOrder';
        plot_title = 'right T1 leg nerve MN clusters (by primary neurite; single linkage)';
    elseif strcmp(nerve, 'an')
        load('an_rsingleHcT1primOrder.mat')
        hcOrder = an_rsingleHcT1primOrder';
        nnames = an_rsingleHcT1primOrder';
        plot_title = 'right T1 accessory leg nerve MN clusters (by primary neurite; single linkage)';
    elseif strcmp(nerve, 'vn')
        load('vn_rsingleHcT1primOrder.mat')
        hcOrder = vn_rsingleHcT1primOrder';
        nnames = vn_rsingleHcT1primOrder';
        plot_title = 'right T1 ventral nerve MN clusters (by primary neurite; single linkage)';
    elseif strcmp(nerve, 'dn')
        load('dn_rsingleHcT1primOrder.mat')
        hcOrder = dn_rsingleHcT1primOrder';
        nnames = dn_rsingleHcT1primOrder';
        plot_title = 'right T1 dorsal nerve MN clusters (by primary neurite; single linkage)';
    end
end

%%
[Lia,Locb] = ismember(hcOrder,lrT1primNblast88Names);

% build matrix sorted by hc order
rM = [];

for i = 1:size(Locb,1)
       
        for j = 1:size(Locb,1)
        rM(i,j) = lrT1primNblast88(Locb(i),Locb(j));
        
        end
    
end

% for labels by bundle in hierarch order
bLables = [];

for i = 1:size(Locb,1)
    
     bLables{i,1} = lrT1primNblast88LUT{Locb(i),4};
     
end

% plot with imagesc

figure;h = imagesc(rM);
axis square
% set(gca, 'CLim', [-1, 1]);


ax = gca;
%// adjust position of ticks
set(ax,'XTick', (1:size(rM,2)) )
set(ax,'YTick', (1:size(rM,1)) )
ax.TickLength = [0 0];
%// set labels
set(ax,'XTickLabel',bLables)
xtickangle(90)
set(ax,'YTickLabel',nnames)
colorbar('location','EastOutside');
title(plot_title)
    
set(gcf,'renderer','painters');

