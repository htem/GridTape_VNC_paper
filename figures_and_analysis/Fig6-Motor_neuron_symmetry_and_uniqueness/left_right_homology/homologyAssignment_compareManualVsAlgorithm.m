% Assignment of left-right pairs of front leg motor neurons from the Female
% Adult Nerve Cord EM dataset. Pairs are assigned to be globally optimal
% based on similarity scores, then the results are compared with pair
% assignments made by human experts. 
% Code based on Hildebrand et al. 2017 Nature

% Pick one of the following two lines, to select which analysis to run
%input_folder = 'inputFiles_primaryNeuritesOnly';
input_folder = 'inputFiles_allNeurites';

% Neuron similarity scores (NBLAST, see Costa et al. 2016 Neuron) were
% generated using the neuron similarity widget within CATMAID.
% Scores exported from CATMAID can be directly used here.
scores_file = strcat(input_folder, filesep, 'similarity_scores.csv');
similarity_scores_raw = importdata(scores_file);
similarity_scores = similarity_scores_raw.data;

% You must provide a list of identifiers for each neuron in the scores file.
% The simplest way to do this is just use the first column of the scores
% file (which are CATMAID skeleton IDs if you generated the scores using
% CATMAID) as the neuron identifiers. To do that, just put the first column
% of similarity_scores.csv into a text file named similarity_scores_identifiers.txt.
% However, in the analysis run here, the neuron names were used as
% identifiers instead, so this identifiers file lists the neuron names in
% an order matching their order in the similarity_scores.csv file.
id_file = strcat(input_folder, filesep, 'similarity_scores_identifiers.txt');
identifiers = importdata(id_file);

% Left-right homologous pairs of motor neurons were identified by human experts.
% See README.md for description of file format.
homologyFile = strcat(input_folder, filesep, 'neurons_ordered_by_homology.txt');
S = importdata(homologyFile);


col_containing_identifiers = 1;
col_containing_labels = 4; % If different columns contain different types of labels,
                           % select the column you want to use via this variable

iskels = zeros(1,length(S));
iskelnames = cell(1,length(S));
if iscell(S)
    for i = 1:length(S)
        ss = strsplit(S{i}, ' ');
        iskels(i) = str2double(ss{col_containing_identifiers});
        iskelnames{i} = ss{col_containing_labels};
    end
elseif isnumeric(S)
    for i = 1:length(S)
        iskels(i) = S(i);
        % set name to skelID if no name in file
        iskelnames{i} = S(i);
    end
end


%% Pull out score matrix indexes of requested neurons
fprintf('Building cost matrix from files\n')

[sLo, sIdxB] = ismember(iskels, identifiers);
% pull out scores from the requested indexes
selected_scores = similarity_scores(sIdxB, sIdxB);

% Average left-right and right-left scores
iskelsLen = length(iskels);
lIndx = 1:round(iskelsLen/2);
rIndx = round(iskelsLen/2)+1:iskelsLen;

l2r_selected_scores = selected_scores(lIndx, rIndx);
r2l_selected_scores = selected_scores(rIndx, lIndx);

selected_scores_symmetric = (l2r_selected_scores + r2l_selected_scores') / 2;

costs = 1 - selected_scores_symmetric;


% reorganize cost matrix to have left on vertical axis 
costs_reformatted = flipud(rot90(costs,1));

%% Run globally-optimal pairwise assignment algorithm
fprintf('Running munkres algorithm (globally-optimal pairwise assignment)\n')
[assignments_munkres, global_cost_munkres] = munkres(costs_reformatted);


%% --------------------------------------------------
fprintf('Displaying cost matrix with matches (black) and mismatches (red) indicated\n');

assignment_comparison = [1:length(assignments_munkres); assignments_munkres]';
figure; clf;
names_ordered_L = iskelnames(1:round(length(iskelnames)/2));
names_ordered_R = iskelnames(round(length(iskelnames)/2)+1:end);
colormap = parula;%flipud(double(parula));
matrix_to_plot = selected_scores_symmetric; %costs_reformatted
min_val = min(matrix_to_plot, [], 'all'); %min(costs, [], 'all')
max_val = max(matrix_to_plot, [], 'all'); %max(costs, [], 'all')
heatmapcust(matrix_to_plot, names_ordered_R(:) ,names_ordered_L(:),...
    [], 'ColorBar',1, 'GridLines','-',...
    'TickAngle',270, 'ShowAllTicks',1, 'UseLogColormap',false,...
    'Colormap',colormap, 'MaxColorValue',max_val, 'MinColorValue',min_val);
%    'Colormap',hmcolmap,'MaxColorValue',1,'MinColorValue',0);
%    'Colormap',hmcolmap);

axis square
ax = gca;
ax.TickLength = [0 0];
star_size = 12;

matches = 0;
mismatches = 0;
for c=1:length(assignment_comparison)
    rectpos = horzcat([(assignment_comparison(c,1)-1) (assignment_comparison(c,2)-1)]+0.5,[1 1]);
    %textpos = [(assignment_comparison(c,1)) (assignment_comparison(c,2)+0.25)];
    textpos = [(assignment_comparison(c,1)) (assignment_comparison(c,2)+0.44)]; %For star size 12
    %textpos = [(assignment_comparison(c,1)-0.01) (assignment_comparison(c,2)+0.515)]; %For star size 15
    %textpos = [(assignment_comparison(c,1)+0.025) (assignment_comparison(c,2)+0.655)]; %For star size 20
    if assignment_comparison(c,2) == assignment_comparison(c,1)
        rectangle('Position',rectpos,'EdgeColor','k','LineWidth',1)
        %fprintf('match\n')
        text('Position',textpos,'String','*','Color','k',...
            'FontSize',star_size,'FontUnits','normalized',...
            'HorizontalAlignment','center','VerticalAlignment','middle');
        matches = matches + 1;
    else
        rectangle('Position',rectpos,'EdgeColor','k','LineWidth',1)
        %fprintf('mismatch\n')
        text('Position',textpos,'String','*','Color','r',...
            'FontSize',star_size,'FontUnits','normalized',...
            'HorizontalAlignment','center','VerticalAlignment','middle');
        mismatches = mismatches + 1;
    end
end

matches
mismatches

set(gcf,'renderer','painters');

