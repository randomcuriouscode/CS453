all: pdf

figures:
	mkdir figures

plot_figures: figures plot_figure.m
	octave plot_figure.m

figures/figure.tex: plot_figures

pdf: figures/figure.tex lecture-notes-template.tex
	pdflatex lecture-notes-template.tex

clean:
	rm -f *.aux *.out *.log *.pdf figures/*
