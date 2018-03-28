% Use Octave to run this script.

% Generate some data.
angles = -2*pi:0.01*pi:2*pi;
c = cos(angles);
s = sin(angles);

% Plot figure.
plot(angles, [c' s'], 'linewidth', 2);
axis([-2*pi, 2*pi, -1.1, 1.1]);
grid on;

% Set figure sizes for paper.
set(gcf, 'paperunits', 'centimeters');
set(gcf, 'paperposition', [1 1 12 8]);

% Generate axis labels, legend.
xlabel('Angle, $\theta$ (radians)');
ylabel('Deflection ($m$)'); 
[legh,objh,outh,outm] = legend('$\cos(\theta)$', '$\sin(\theta)$'); 
set(objh,'linewidth',2);
set(legh,"fontweight","bold");

% Save EPS and Latex file.
print('figures/figure.eps', '-depslatex');

