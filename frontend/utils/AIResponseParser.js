/**
 * AIResponseParser - Utility to parse AI responses and separate code from text
 * Extracts code blocks, inline code, and descriptive text from AI suggestions
 */

class AIResponseParser {
  /**
   * Parse AI response to separate description from code
   * @param {string} rawResponse - Raw AI response text
   * @returns {Object} Parsed response with separated components
   */
  static parseResponse(rawResponse) {
    if (!rawResponse || typeof rawResponse !== 'string') {
      return {
        description: '',
        codeBlocks: [],
        inlineCode: [],
        hasCode: false
      };
    }

    const codeBlocks = [];
    const inlineCode = [];
    let description = rawResponse;

    // Extract markdown code blocks (```language\ncode\n```)
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    let match;
    let blockIndex = 0;

    while ((match = codeBlockRegex.exec(rawResponse)) !== null) {
      const language = match[1] || 'text';
      const code = match[2].trim();
      const placeholder = `__CODE_BLOCK_${blockIndex}__`;

      codeBlocks.push({
        language,
        code,
        placeholder,
        startIndex: match.index,
        endIndex: match.index + match[0].length
      });

      // Replace code block with placeholder in description
      description = description.replace(match[0], placeholder);
      blockIndex++;
    }

    // Extract inline code (`code`)
    const inlineCodeRegex = /`([^`]+)`/g;
    let inlineMatch;
    let inlineIndex = 0;

    while ((inlineMatch = inlineCodeRegex.exec(description)) !== null) {
      const code = inlineMatch[1];
      const placeholder = `__INLINE_CODE_${inlineIndex}__`;

      inlineCode.push({
        code,
        placeholder,
        startIndex: inlineMatch.index,
        endIndex: inlineMatch.index + inlineMatch[0].length
      });

      // Replace inline code with placeholder
      description = description.replace(inlineMatch[0], placeholder);
      inlineIndex++;
    }

    // Clean up description
    description = description
      .replace(/__CODE_BLOCK_\d+__/g, '') // Remove code block placeholders
      .replace(/__INLINE_CODE_\d+__/g, '') // Remove inline code placeholders
      .replace(/\n{3,}/g, '\n\n') // Remove excessive newlines
      .trim();

    return {
      description,
      codeBlocks,
      inlineCode,
      hasCode: codeBlocks.length > 0 || inlineCode.length > 0,
      originalText: rawResponse
    };
  }

  /**
   * Parse suggestion to extract code examples
   * @param {Object} suggestion - Suggestion object with message/suggestion text
   * @returns {Object} Parsed suggestion with separated code and text
   */
  static parseSuggestion(suggestion) {
    if (!suggestion) {
      return {
        text: '',
        code: null,
        hasCode: false
      };
    }

    const suggestionText = suggestion.suggestion || suggestion.message || '';
    const parsed = this.parseResponse(suggestionText);

    return {
      text: parsed.description,
      code: parsed.codeBlocks.length > 0 ? parsed.codeBlocks[0].code : null,
      codeLanguage: parsed.codeBlocks.length > 0 ? parsed.codeBlocks[0].language : null,
      allCodeBlocks: parsed.codeBlocks,
      inlineCode: parsed.inlineCode,
      hasCode: parsed.hasCode,
      originalSuggestion: suggestion
    };
  }

  /**
   * Extract code snippets from text
   * @param {string} text - Text containing code
   * @returns {Array} Array of code snippets
   */
  static extractCodeSnippets(text) {
    if (!text) return [];

    const parsed = this.parseResponse(text);
    return parsed.codeBlocks.map(block => ({
      language: block.language,
      code: block.code
    }));
  }

  /**
   * Remove code from text, leaving only description
   * @param {string} text - Text containing code
   * @returns {string} Text without code blocks
   */
  static removeCode(text) {
    if (!text) return '';

    const parsed = this.parseResponse(text);
    return parsed.description;
  }

  /**
   * Format code block for display
   * @param {string} code - Code to format
   * @param {string} language - Programming language
   * @returns {string} Formatted code block
   */
  static formatCodeBlock(code, language = 'text') {
    if (!code) return '';
    return `\`\`\`${language}\n${code}\n\`\`\``;
  }

  /**
   * Parse issue/suggestion object to separate components
   * @param {Object} issue - Issue object from analysis
   * @returns {Object} Parsed issue with separated components
   */
  static parseIssue(issue) {
    if (!issue) return null;

    const messageParsed = this.parseResponse(issue.message || '');
    const suggestionParsed = issue.suggestion 
      ? this.parseResponse(issue.suggestion)
      : { description: '', codeBlocks: [], hasCode: false };

    return {
      ...issue,
      messageText: messageParsed.description,
      messageCode: messageParsed.codeBlocks,
      suggestionText: suggestionParsed.description,
      suggestionCode: suggestionParsed.codeBlocks,
      hasCodeInMessage: messageParsed.hasCode,
      hasCodeInSuggestion: suggestionParsed.hasCode,
      codeExample: issue.codeExample || (suggestionParsed.codeBlocks.length > 0 
        ? suggestionParsed.codeBlocks[0].code 
        : null)
    };
  }

  /**
   * Parse multiple issues/suggestions
   * @param {Array} issues - Array of issue objects
   * @returns {Array} Array of parsed issues
   */
  static parseIssues(issues) {
    if (!Array.isArray(issues)) return [];
    return issues.map(issue => this.parseIssue(issue));
  }

  /**
   * Detect if text contains code
   * @param {string} text - Text to check
   * @returns {boolean} True if text contains code
   */
  static containsCode(text) {
    if (!text) return false;

    // Check for markdown code blocks
    if (/```[\s\S]*?```/.test(text)) return true;

    // Check for inline code
    if (/`[^`]+`/.test(text)) return true;

    // Check for common code patterns
    const codePatterns = [
      /function\s+\w+\s*\(/,
      /const\s+\w+\s*=/,
      /let\s+\w+\s*=/,
      /var\s+\w+\s*=/,
      /class\s+\w+/,
      /def\s+\w+\s*\(/,
      /import\s+.*from/,
      /require\s*\(/,
      /#include\s*</,
      /public\s+class/,
      /private\s+\w+/
    ];

    return codePatterns.some(pattern => pattern.test(text));
  }

  /**
   * Split text into paragraphs, preserving code blocks
   * @param {string} text - Text to split
   * @returns {Array} Array of paragraphs and code blocks
   */
  static splitIntoParagraphs(text) {
    if (!text) return [];

    const parsed = this.parseResponse(text);
    const paragraphs = [];

    // Split description into paragraphs
    const textParagraphs = parsed.description
      .split(/\n\n+/)
      .filter(p => p.trim())
      .map(p => ({
        type: 'text',
        content: p.trim()
      }));

    // Interleave text paragraphs and code blocks based on original positions
    let textIndex = 0;
    let codeIndex = 0;

    while (textIndex < textParagraphs.length || codeIndex < parsed.codeBlocks.length) {
      if (textIndex < textParagraphs.length) {
        paragraphs.push(textParagraphs[textIndex]);
        textIndex++;
      }

      if (codeIndex < parsed.codeBlocks.length) {
        paragraphs.push({
          type: 'code',
          content: parsed.codeBlocks[codeIndex].code,
          language: parsed.codeBlocks[codeIndex].language
        });
        codeIndex++;
      }
    }

    return paragraphs;
  }

  /**
   * Clean and normalize AI response text
   * @param {string} text - Text to clean
   * @returns {string} Cleaned text
   */
  static cleanText(text) {
    if (!text) return '';

    return text
      .replace(/\r\n/g, '\n') // Normalize line endings
      .replace(/\t/g, '  ') // Replace tabs with spaces
      .replace(/\n{3,}/g, '\n\n') // Remove excessive newlines
      .replace(/^\s+|\s+$/g, '') // Trim whitespace
      .replace(/\s+$/gm, ''); // Remove trailing whitespace from lines
  }
}

export default AIResponseParser;
