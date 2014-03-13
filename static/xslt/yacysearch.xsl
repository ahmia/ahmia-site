<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:dc="http://purl.org/dc/elements/1.1/" version="1.0">
    <xsl:output method="html"/>
    <xsl:template match='/lol'>

  <html lang="en">
   <head>
    <meta charset="utf-8" />
    <meta name='description' content='Search onion web pages' />
    <meta name='keywords' content='onion domains, hidden services, deep web, search engine, onion pages, onion sites, list, cache, tor, tor2web, index, search, pages, show content' />
    <meta name='author' content='ahmia' />
    <title>Full text hidden service search</title>
    <link rel='stylesheet' type='text/css' href='/static/styles/base_styles.css' />
    <script src='/static/js/jquery.min.js'></script>
    <script src='/static/js/highlight.js'></script>
    <link href='/static/styles/fontstyles/Cagliostro.css' rel='stylesheet' />
    <link href='/static/styles/fontstyles/Bitter.css' rel='stylesheet' />
    <link href='/static/styles/fontstyles/OpenSans.css' rel='stylesheet' />
   </head>
  <body>
   <header class="pagetitle" role="banner">
    <a href="/" title="ahmia.fi home">
     <h1>- Tor Hidden Service (.onion) search -</h1>
     <p class="ahmia">AHMIA.FI</p>
    </a>
   </header>
   <div id="content">
    <h2 style="padding: 5px; float: left; width: 300px;">Full Text Search</h2>
    <div id="search">
     <form action="/find/" id="searchForm" method="get">
      <input style="float: left;" name="s" class="filterinput" id="torsearch" type="text" placeholder="{channel/description}" autofocus="autofocus" />
      <input style="margin-left: 5px; position: absolute;" class="input-add" type="submit" value="Search" />
     </form>
    </div>
    <br style="clear: left;" />
   </div>

   <!-- the result of the search will be rendered inside this list -->
   <ul id="list" class="steps">
	<xsl:apply-templates select='channel/item' />
   </ul>   

   </body>
  </html>

                        
    </xsl:template>
    
    <xsl:template match='item'>
	<li class="hs_site">
	 <h3><a href="{link}"><xsl:value-of select='title'/></a></h3>
	 <div class="infotext">
	  <p class="links">Link: <a href="{link}" ><xsl:value-of select='link' /></a></p>
	  <xsl:value-of select='description' disable-output-escaping="yes"/>
	  <p class="urlinfo"><xsl:value-of select='pubDate' /></p>
         </div>
	</li>	  
    </xsl:template>
    
</xsl:stylesheet>
