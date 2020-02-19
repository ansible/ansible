#!/bin/bash
xsltproc <(cat <<EOF
<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text" encoding="UTF-8" omit-xml-declaration="yes" indent="no" media-type="application/json" />
<xsl:strip-space elements="*" />
  <xsl:template match="/">
    <xsl:text>{</xsl:text>
      <xsl:for-each select="hosts/group">
        "<xsl:value-of select="@name"/>": [ 
          <xsl:for-each select="host">
          "<xsl:value-of select="@name"/>"
            <xsl:if test="position() != last()"> 
              <xsl:text>,</xsl:text> 
            </xsl:if> 
          </xsl:for-each> ]
        <xsl:if test="position() != last()"> 
        <xsl:text>,</xsl:text> 
        </xsl:if>
      </xsl:for-each>
    <xsl:text>}</xsl:text>
</xsl:template>
</xsl:stylesheet>
EOF
) ~/.config/apt-dater/hosts.xml
