import jieba
import jieba.analyse
import networkx as nx
import numpy as np
from collections import defaultdict
import re


class TextSummarizer:
    """文本摘要生成器，基于TextRank算法实现自动文本摘要"""

    def __init__(self, language='chinese'):
        """初始化摘要生成器
        
        Args:
            language (str): 文本语言，支持'chinese'和'english'，默认为'chinese'
        """
        self.language = language
        # 停用词列表
        self.stopwords = {'的', '了', '和', '是', '就', '都', '而', '及', '与', '着', 'the', 'a', 'an', 'and', 'or',
                          'but', 'in', 'on', 'at', 'to'}

    def _split_sentences(self, text):
        """将文本分割成句子
        
        Args:
            text (str): 输入文本
            
        Returns:
            list: 句子列表
        """
        if self.language == 'chinese':
            # 中文按句号、问号、感叹号分句
            pattern = r'[。！？]'
        else:
            # 英文按句号、问号、感叹号分句
            pattern = r'[.!?]'

        sentences = re.split(pattern, text)
        # 过滤空句子
        return [s.strip() for s in sentences if s.strip()]

    def _calculate_similarity(self, sentence1, sentence2):
        """计算两个句子的相似度
        
        Args:
            sentence1 (str): 第一个句子
            sentence2 (str): 第二个句子
            
        Returns:
            float: 相似度分数
        """
        if self.language == 'chinese':
            words1 = [w for w in jieba.cut(sentence1) if w not in self.stopwords]
            words2 = [w for w in jieba.cut(sentence2) if w not in self.stopwords]
        else:
            words1 = [w.lower() for w in sentence1.split() if w.lower() not in self.stopwords]
            words2 = [w.lower() for w in sentence2.split() if w.lower() not in self.stopwords]

        # 创建词频字典
        word_freq1 = defaultdict(int)
        word_freq2 = defaultdict(int)

        for word in words1:
            word_freq1[word] += 1
        for word in words2:
            word_freq2[word] += 1

        # 计算共现词的权重
        common_words = set(words1) & set(words2)
        weight = sum(word_freq1[word] * word_freq2[word] for word in common_words)

        # 使用余弦相似度公式
        if weight == 0:
            return 0

        norm1 = np.sqrt(sum(freq ** 2 for freq in word_freq1.values()))
        norm2 = np.sqrt(sum(freq ** 2 for freq in word_freq2.values()))

        return weight / (norm1 * norm2)

    def _build_similarity_matrix(self, sentences):
        """构建句子相似度矩阵
        
        Args:
            sentences (list): 句子列表
            
        Returns:
            numpy.ndarray: 相似度矩阵
        """
        n = len(sentences)
        similarity_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    similarity_matrix[i][j] = self._calculate_similarity(sentences[i], sentences[j])

        # 归一化处理
        for i in range(n):
            row_sum = similarity_matrix[i].sum()
            if row_sum != 0:
                similarity_matrix[i] = similarity_matrix[i] / row_sum

        return similarity_matrix

    def generate_summary(self, text, ratio=0.3, top_n=None):
        """生成文本摘要
        
        Args:
            text (str): 输入文本
            ratio (float): 摘要占原文的比例，默认0.3
            top_n (int): 返回前n个重要句子，如果设置了这个参数，会忽略ratio
            
        Returns:
            str: 生成的摘要文本
        """
        # 分句
        sentences = self._split_sentences(text)
        if not sentences:
            return ""

        # 如果句子数量太少，直接返回原文
        if len(sentences) <= 3:
            return text

        # 构建相似度矩阵
        similarity_matrix = self._build_similarity_matrix(sentences)

        # 使用NetworkX创建图并计算PageRank值
        nx_graph = nx.from_numpy_array(similarity_matrix)
        scores = nx.pagerank(nx_graph)

        # 根据分数对句子排序
        ranked_sentences = [(score, sentence) for sentence, score in zip(sentences, scores.values())]
        ranked_sentences.sort(reverse=True)

        # 确定要选择的句子数量
        if top_n is not None:
            n_sentences = min(top_n, len(ranked_sentences))
        else:
            n_sentences = max(3, int(len(sentences) * ratio))

        # 按原文顺序重新排列选中的句子
        selected_sentences = ranked_sentences[:n_sentences]
        selected_sentences.sort(key=lambda x: sentences.index(x[1]))

        # 生成摘要文本
        if self.language == 'chinese':
            summary = '。'.join(sentence for _, sentence in selected_sentences) + '。'
        else:
            summary = '. '.join(sentence for _, sentence in selected_sentences) + '.'

        return summary

    def get_keywords(self, text, top_k=10):
        """提取文本关键词
        
        Args:
            text (str): 输入文本
            top_k (int): 返回前k个关键词，默认10个
            
        Returns:
            list: 关键词列表
        """
        if self.language == 'chinese':
            # 使用jieba的TextRank算法提取关键词
            keywords = jieba.analyse.textrank(text, topK=top_k)
        else:
            # 英文文本使用TF-IDF提取关键词
            words = [w.lower() for w in text.split() if w.lower() not in self.stopwords]
            word_freq = defaultdict(int)
            for word in words:
                word_freq[word] += 1
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_k]
            keywords = [word for word, _ in keywords]

        return keywords


def main():
    # 示例用法
    text = """
    自然语言处理是人工智能的一个重要分支。它主要研究计算机处理自然语言的各种理论和方法。
    自然语言处理的应用非常广泛，包括机器翻译、信息检索、文本分类、问答系统等。
    近年来，深度学习技术的发展大大推动了自然语言处理的进步。
    各种新的模型和方法不断被提出，显著提高了处理效果。
    这使得自然语言处理技术在实际应用中发挥着越来越重要的作用。
    """

    # 创建摘要生成器实例
    summarizer = TextSummarizer(language='chinese')

    # 生成摘要
    summary = summarizer.generate_summary(text, ratio=0.3)
    print("\n生成的摘要:")
    print(summary)

    # 提取关键词
    keywords = summarizer.get_keywords(text, top_k=5)
    print("\n关键词:")
    print(", ".join(keywords))


if __name__ == "__main__":
    main()
