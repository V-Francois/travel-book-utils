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
\definecolor{tbsecondary}{HTML}{2F6F73}
\definecolor{tbpaper}{HTML}{FAFAF7}
\definecolor{tbsoft}{HTML}{ECE8DF}

\pagecolor{tbpaper}
\color{tbink}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.65\baselineskip}
\OnehalfSpacing
\raggedbottom
\setcounter{secnumdepth}{0}
\setcounter{tocdepth}{1}
\setsecheadstyle{\sffamily\Large\bfseries\color{tbaccent}}

\captionsetup{
  font={small,sf},
  labelformat=empty,
  justification=raggedright,
  singlelinecheck=false,
  skip=6pt
}

\makeatletter
\newif\iftb@foliosenabled
\newif\iftb@suppressfolio
\tb@foliosenabledfalse
\tb@suppressfoliofalse

\let\tb@oldpagenumbering\pagenumbering
\renewcommand{\pagenumbering}[1]{%
  \tb@oldpagenumbering{#1}%
  \global\tb@foliosenabledtrue
}

\newcommand{\travelbookfolioson}{\global\tb@foliosenabledtrue}
\newcommand{\travelbookfoliosoff}{\global\tb@foliosenabledfalse}
\newcommand{\tb@suppressfolioonthispage}{\global\tb@suppressfoliotrue}

\newcommand{\tb@edgefolio}{%
  \begin{tikzpicture}[remember picture,overlay]
    \ifodd\value{page}
      \fill[tbaccent]
        (current page.south east) rectangle ++(-9mm,7mm);
      \node[
        anchor=south east,
        text=white,
        font=\sffamily\scriptsize\bfseries,
        inner sep=0pt,
        minimum width=9mm,
        minimum height=7mm
      ] at (current page.south east) {\thepage};
    \else
      \fill[tbaccent]
        (current page.south west) rectangle ++(9mm,7mm);
      \node[
        anchor=south west,
        text=white,
        font=\sffamily\scriptsize\bfseries,
        inner sep=0pt,
        minimum width=9mm,
        minimum height=7mm
      ] at (current page.south west) {\thepage};
    \fi
  \end{tikzpicture}%
}
\AddToShipoutPictureFG{%
  \iftb@foliosenabled
    \iftb@suppressfolio
    \else
      \tb@edgefolio
    \fi
  \fi
  \global\tb@suppressfoliofalse
}

\makepagestyle{travelbook}
\makeevenfoot{travelbook}{}{}{}
\makeoddfoot{travelbook}{}{}{}
\makeheadrule{travelbook}{0pt}{0pt}
\pagestyle{travelbook}
\aliaspagestyle{plain}{travelbook}
\aliaspagestyle{chapter}{travelbook}

\newcommand{\travelbookaccent}[1]{\colorlet{tbaccent}{#1}}
\newcommand{\travelbooksecondaryaccent}[1]{\colorlet{tbsecondary}{#1}}
\newcommand{\tb@ifnotempty}[2]{%
  \if\relax\detokenize{#1}\relax\else#2\fi
}
\newcommand{\tbkicker}[1]{%
  {\sffamily\footnotesize\bfseries\color{tbsecondary}\MakeUppercase{#1}}\par\vspace{0.4\baselineskip}%
}
\newcommand{\tbjourneytitle}[1]{%
  {\sffamily\footnotesize\bfseries\color{tbsecondary}#1}\par\vspace{0.4\baselineskip}%
}

\newcommand{\tbcaption}[1]{%
  \par\vspace{0.35\baselineskip}%
  {\sffamily\small\color{tbmuted}#1\par}%
}

\newcounter{journeystep}

\NewDocumentEnvironment{journey}{O{}}{%
  \par\bigskip
  \setcounter{journeystep}{0}%
  \tb@ifnotempty{#1}{\tbjourneytitle{#1}}%
}{%
  \par\bigskip
}

\newcommand{\tbjourneyroute}[2]{%
  #1\tb@ifnotempty{#2}{\,\(\rightarrow\)\,#2}%
}

\NewDocumentCommand{\journeystep}{m m +m}{%
  \refstepcounter{journeystep}%
  \par\noindent
  {\tikz[baseline=-0.55ex]{\draw[tbsecondary,line width=1.8pt] (0,0) -- (8mm,0);}}%
  \hspace{2mm}%
  {\sffamily\bfseries\color{tbsecondary}\tbjourneyroute{#1}{#2}}%
  \quad
  #3\par\vspace{0.45\baselineskip}%
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
  \tb@suppressfolioonthispage
  \AddToShipoutPictureBG*{%
    \begin{tikzpicture}[remember picture,overlay]
      \clip (current page.south west) rectangle (current page.north east);
      \node[anchor=center,inner sep=0pt] at (current page.center)
        {\tbpagegraphic[#1]{#2}};
      \fill[black,opacity=0.0] (current page.south west) rectangle (current page.north east);
      \fill[tbaccent,opacity=0.92]
        ([xshift=13mm,yshift=-20mm]current page.north west)
        rectangle ++(1.8mm,-26mm);
      \node[anchor=north west,text width=.78\paperwidth,align=left]
        at ([xshift=18mm,yshift=-20mm]current page.north west)
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
  \tb@suppressfolioonthispage
  \AddToShipoutPictureBG*{%
    \begin{tikzpicture}[remember picture,overlay]
      \clip (current page.south west) rectangle (current page.north east);
      \node[anchor=center,inner sep=0pt,rotate=#1] at (current page.center)
        {\tbpagegraphicbox[#2]{#3}{\paperheight}{\paperwidth}};
      \fill[black,opacity=0.28] (current page.south west) rectangle (current page.north east);
      \fill[tbaccent,opacity=0.92]
        ([xshift=13mm,yshift=-20mm]current page.north west)
        rectangle ++(1.8mm,-26mm);
      \node[anchor=north west,text width=.74\paperwidth,align=left]
        at ([xshift=18mm,yshift=-20mm]current page.north west)
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
  \tb@suppressfolioonthispage
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
  \tb@suppressfolioonthispage
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
  \tb@suppressfolioonthispage
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
    colback=tbsecondary!4!white,
    colframe=tbsecondary!20!white,
    boxrule=.5pt,
    arc=0pt,
    left=6mm,
    right=6mm,
    top=5mm,
    bottom=5mm,
    borderline west={1.8pt}{0pt}{tbsecondary}
  ]
  \tbkicker{#1}
  \ignorespaces
}{%
\end{tcolorbox}
}

\makeatother
\endinput
