\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{travelbook}[2026/07/01 Editorial A5 photo book class]

\LoadClass[11pt,a5paper,openany]{memoir}

\RequirePackage[a5paper,portrait,inner=15mm,outer=12mm,top=14mm,bottom=17mm,includefoot]{geometry}
\RequirePackage{iftex}
\RequirePackage{graphicx}
\RequirePackage{xparse}
\RequirePackage{xcolor}
\RequirePackage{tikz}
\RequirePackage{eso-pic}
\RequirePackage{caption}
\RequirePackage{ragged2e}
\RequirePackage{microtype}
\RequirePackage{needspace}
\RequirePackage[most]{tcolorbox}

\ifPDFTeX
  \RequirePackage[T1]{fontenc}
  \RequirePackage[utf8]{inputenc}
  \RequirePackage{lmodern}
\else
  \RequirePackage{fontspec}
  \setmainfont{TeX Gyre Pagella}
  \setsansfont{TeX Gyre Heros}
\fi

\definecolor{tbink}{HTML}{171717}
\definecolor{tbmuted}{HTML}{6E7479}
\definecolor{tbaccent}{HTML}{C84D36}
\definecolor{tbpaper}{HTML}{FAFAF7}
\definecolor{tbsoft}{HTML}{ECE8DF}

\pagecolor{tbpaper}
\color{tbink}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.65\baselineskip}
\OnehalfSpacing
\raggedbottom
\setcounter{secnumdepth}{1}
\setcounter{tocdepth}{1}
\renewcommand{\thesection}{\arabic{section}}
\setsecheadstyle{\sffamily\Large\bfseries\color{tbaccent}}

\captionsetup{
  font={small,sf},
  labelformat=empty,
  justification=raggedright,
  singlelinecheck=false,
  skip=6pt
}

\newcommand{\tbfolio}{%
  \tikz[baseline=(n.base)]{
    \node[
      circle,
      fill=tbaccent,
      text=white,
      inner sep=0pt,
      minimum size=6.5mm,
      font=\sffamily\scriptsize\bfseries
    ] (n) {\thepage};
  }%
}

\makepagestyle{travelbook}
\makeevenfoot{travelbook}{\tbfolio}{}{}
\makeoddfoot{travelbook}{}{}{\tbfolio}
\makeheadrule{travelbook}{0pt}{0pt}
\pagestyle{travelbook}
\aliaspagestyle{plain}{travelbook}
\aliaspagestyle{chapter}{travelbook}

\newcommand{\travelbookaccent}[1]{\colorlet{tbaccent}{#1}}
\newcommand{\tb@ifnotempty}[2]{%
  \if\relax\detokenize{#1}\relax\else#2\fi
}
\newcommand{\tbkicker}[1]{%
  {\sffamily\footnotesize\bfseries\color{tbaccent}\MakeUppercase{#1}}\par\vspace{0.4\baselineskip}%
}

\newcommand{\tbcaption}[1]{%
  \par\vspace{0.35\baselineskip}%
  {\sffamily\small\color{tbmuted}#1\par}%
}

\newsavebox{\tb@pagegraphicbase}
\newsavebox{\tb@pagegraphicscaled}
\NewDocumentCommand{\tbpagegraphicbox}{O{} m m m}{%
  \sbox{\tb@pagegraphicbase}{\includegraphics[#1]{#2}}%
  \sbox{\tb@pagegraphicscaled}{\resizebox{#3}{!}{\usebox{\tb@pagegraphicbase}}}%
  \ifdim\dimexpr\ht\tb@pagegraphicscaled+\dp\tb@pagegraphicscaled\relax<#4
    \resizebox{!}{#4}{\usebox{\tb@pagegraphicbase}}%
  \else
    \usebox{\tb@pagegraphicscaled}%
  \fi
}
\NewDocumentCommand{\tbpagegraphic}{O{} m}{%
  \tbpagegraphicbox[#1]{#2}{\paperwidth}{\paperheight}%
}

\NewDocumentCommand{\tbimage}{O{} m O{}}{%
  \begin{figure}[p]
    \centering
    \includegraphics[width=\linewidth,#1]{#2}
    \tb@ifnotempty{#3}{\caption{#3}}
  \end{figure}%
}

\NewDocumentCommand{\makebookcover}{O{} m m m}{%
  \cleardoublepage
  \thispagestyle{empty}
  \AddToShipoutPictureBG*{%
    \begin{tikzpicture}[remember picture,overlay]
      \clip (current page.south west) rectangle (current page.north east);
      \node[anchor=center,inner sep=0pt] at (current page.center)
        {\tbpagegraphic[#1]{#2}};
      \fill[black,opacity=0.0] (current page.south west) rectangle (current page.north east);
      \fill[tbaccent,opacity=0.92]
        ([xshift=13mm,yshift=19mm]current page.south west)
        rectangle ++(1.8mm,52mm);
      \node[anchor=south west,text width=.74\paperwidth,align=left]
        at ([xshift=18mm,yshift=21mm]current page.south west)
        {{\sffamily\fontsize{29}{31}\selectfont\bfseries\color{white}#3\par}
         \vspace{5mm}
         {\sffamily\large\color{white!88}#4\par}};
    \end{tikzpicture}%
  }%
  \null\newpage
}

\NewDocumentCommand{\makebookcoverrotated}{O{-90} O{} m m m}{%
  \cleardoublepage
  \thispagestyle{empty}
  \AddToShipoutPictureBG*{%
    \begin{tikzpicture}[remember picture,overlay]
      \clip (current page.south west) rectangle (current page.north east);
      \node[anchor=center,inner sep=0pt,rotate=#1] at (current page.center)
        {\tbpagegraphicbox[#2]{#3}{\paperheight}{\paperwidth}};
      \fill[black,opacity=0.28] (current page.south west) rectangle (current page.north east);
      \fill[tbaccent,opacity=0.92]
        ([xshift=13mm,yshift=19mm]current page.south west)
        rectangle ++(1.8mm,52mm);
      \node[anchor=south west,text width=.74\paperwidth,align=left]
        at ([xshift=18mm,yshift=21mm]current page.south west)
        {{\sffamily\fontsize{29}{31}\selectfont\bfseries\color{white}#4\par}
         \vspace{5mm}
         {\sffamily\large\color{white!88}#5\par}};
    \end{tikzpicture}%
  }%
  \null\newpage
}

\NewDocumentCommand{\makebookbackcover}{O{} m m}{%
  \cleardoublepage
  \thispagestyle{empty}
  \AddToShipoutPictureBG*{%
    \begin{tikzpicture}[remember picture,overlay]
      \clip (current page.south west) rectangle (current page.north east);
      \node[anchor=center,inner sep=0pt] at (current page.center)
        {\tbpagegraphic[#1]{#2}};
      \fill[black,opacity=0.38] (current page.south west) rectangle (current page.north east);
      \node[anchor=south west,text width=.72\paperwidth,align=left]
        at ([xshift=15mm,yshift=18mm]current page.south west)
        {{\sffamily\Large\color{white}#3\par}};
    \end{tikzpicture}%
  }%
  \null\newpage
}

\NewDocumentCommand{\fullpagephoto}{O{} O{width=\paperwidth} m}{%
  \cleardoublepage
  \thispagestyle{empty}
  \AddToShipoutPictureBG*{%
    \begin{tikzpicture}[remember picture,overlay]
      \clip (current page.south west) rectangle (current page.north east);
      \node[anchor=center,inner sep=0pt] at (current page.center)
        {\includegraphics[#2]{#3}};
      \tb@ifnotempty{#1}{%
        \fill[black,opacity=0.46]
          ([yshift=0mm]current page.south west) rectangle
          ([yshift=26mm]current page.south east);
        \node[anchor=south west,text width=.82\paperwidth,align=left]
          at ([xshift=12mm,yshift=8mm]current page.south west)
          {{\sffamily\small\color{white}#1\par}};
      }%
    \end{tikzpicture}%
  }%
  \null\newpage
}

\NewDocumentCommand{\chapterspread}{O{} m m m}{%
  \cleardoublepage
  \thispagestyle{empty}
  \AddToShipoutPictureBG*{%
    \begin{tikzpicture}[remember picture,overlay]
      \clip (current page.south west) rectangle (current page.north east);
      \node[anchor=center,inner sep=0pt] at (current page.center)
        {\tbpagegraphic[#1]{#4}};
      \fill[black,opacity=0.34] (current page.south west) rectangle (current page.north east);
      \fill[tbaccent] ([xshift=13mm,yshift=-18mm]current page.north west) rectangle ++(42mm,3mm);
      \node[anchor=north west,text width=.76\paperwidth,align=left]
        at ([xshift=13mm,yshift=-25mm]current page.north west)
        {{\sffamily\fontsize{27}{29}\selectfont\bfseries\color{white}#2\par}
         \vspace{4mm}
         {\sffamily\large\color{white!90}#3\par}};
    \end{tikzpicture}%
  }%
  \null\newpage
}

\NewDocumentCommand{\twophotos}{O{} m m O{} m m}{%
  \clearpage
  \thispagestyle{travelbook}
  \begin{minipage}[t]{.48\textwidth}
    \includegraphics[width=\linewidth,#1]{#2}
    \tbcaption{#3}
  \end{minipage}\hfill
  \begin{minipage}[t]{.48\textwidth}
    \includegraphics[width=\linewidth,#4]{#5}
    \tbcaption{#6}
  \end{minipage}
  \clearpage
}

\NewDocumentCommand{\threephotos}{m m m m m m}{%
  \clearpage
  \thispagestyle{travelbook}
  \begin{minipage}[t]{\textwidth}
    \includegraphics[width=\linewidth]{#1}
    \tbcaption{#2}
  \end{minipage}
  \vfill
  \begin{minipage}[t]{.48\textwidth}
    \includegraphics[width=\linewidth]{#3}
    \tbcaption{#4}
  \end{minipage}\hfill
  \begin{minipage}[t]{.48\textwidth}
    \includegraphics[width=\linewidth]{#5}
    \tbcaption{#6}
  \end{minipage}
  \clearpage
}

\NewDocumentEnvironment{travelnote}{O{Note}}{%
  \Needspace{6\baselineskip}
  \begin{tcolorbox}[
    enhanced,
    colback=white,
    colframe=tbsoft,
    boxrule=.5pt,
    arc=0pt,
    left=6mm,
    right=6mm,
    top=5mm,
    bottom=5mm,
    borderline west={1.8pt}{0pt}{tbaccent}
  ]
  \tbkicker{#1}
  \ignorespaces
}{%
  \end{tcolorbox}
}

\endinput
