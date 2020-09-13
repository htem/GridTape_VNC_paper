%% vnc t1 motor neuron similarity matrix PRIMARY BRANCHES only
% starting with csv export of CATMAID neuron similarity results gives NBLAST scores as a
% matrix with skeleton ID headers. This matrix has left, right ("flippped" mixed). 
% Scores and header separated
load('lrT1primNblast.mat');

% JMS's pymaid script was used to get names, bundles corresponding to these skeleton IDs in the
% transformed into template project
load('lrT1primNblastNames.mat');
load('lrT1primNblastLUT.mat');

%% Just left T1mns, now broken up by nerve

% Hierarchical clustering with single linkage was performed on similarity 
% scores for motor neurons of each peripheral nerve using the SciPy Python 
% package by JMS

% ln: main leg nerve, an: accessory leg nerve, vn: ventral nerve, dn: dorsal nerve

% load('ln_lsingleHcT1primOrder.mat')
% hcOrder = ln_lsingleHcT1primOrder';
% nnames = ln_lsingleHcT1primOrder';

load('an_lsingleHcT1primOrder.mat')
hcOrder = an_lsingleHcT1primOrder';
nnames = an_lsingleHcT1primOrder';

% load('vn_lsingleHcT1primOrder.mat')
% hcOrder = vn_lsingleHcT1primOrder';
% nnames = vn_lsingleHcT1primOrder';

% load('dn_lsingleHcT1primOrder.mat')
% hcOrder = dn_lsingleHcT1primOrder';
% nnames = dn_lsingleHcT1primOrder';


[Lia,Locb] = ismember(hcOrder,lrT1primNblastNames);

% build matrix sorted by hc order
rM = [];

for i = 1:size(Locb,1)
       
        for j = 1:size(Locb,1)
        rM(i,j) = lrT1primNblast(Locb(i),Locb(j));
        
        end
    
end

% for labels by bundle in hierarch order
bLables = [];

for i = 1:size(Locb,1)
    
     bLables{i,1} = lrT1primNblastLUT{Locb(i),4};
     
end

%% plot with imagesc

figure;h = imagesc(rM);
axis square
% set(gca, 'CLim', [-1, 1]);


ax = gca;
%// adjust position of ticks
set(ax,'XTick', (1:size(rM,2)) )
set(ax,'YTick', (1:size(rM,1)) )
ax.TickLength = [0 0]
%// set labels
set(ax,'XTickLabel',bLables)
xtickangle(90)
set(ax,'YTickLabel',nnames)
colorbar('location','EastOutside');
% title('left T1 MN clusters (by main branch)');
% title('left T1 leg nerve MN clusters (by primary neurite; Single linkage)');
title('left T1 acc leg nerve MN clusters (by primary neurite; Single linkage)');
% title('left T1 ventral nerve MN clusters (by primary neurite; Single linkage)');
% title('left T1 dorsal nerve MN clusters (by primary neurite; Single linkage)');
    
set(gcf,'renderer','painters');
