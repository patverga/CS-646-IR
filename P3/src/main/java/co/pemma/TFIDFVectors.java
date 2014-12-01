package co.pemma;

import cc.factorie.app.strings.PorterStemmer;
//import org.apache.mahout.math.SequentialAccessSparseVector;
//import org.apache.mahout.math.Vector;
import cc.factorie.la.SparseTensor1;
import org.javatuples.Pair;

import java.util.*;
import java.util.Map.Entry;
import java.util.concurrent.ConcurrentHashMap;


public class TFIDFVectors
{
    // size of ngram window (only supports a single size ngram currently)
    final static int N_GRAM_SIZE = 4;
    // how many documents must ngram occur in to be considered
    final static int MIN_DOC_OCCURANCES = 1;
    // only use most frequent ngrams (use really big number to disable)
    final static int TOP_NGRAM_K = 100000; //100k
    // convert all ngrams to lower case
    final static boolean ALL_LOWER = false;
    // use iverse document frequency
    final static boolean IDF = true;
//    // return a concurrent hash map, false returns regular hashmap
//    final static boolean THREAD_SAFE = true;


    public static List<SparseTensor1> run(List<String> inputPosts)
    {
        return run(inputPosts, TokenType.STEMS);
    }

    public static List<SparseTensor1> run(List<String> inputPosts, TokenType token)
    {
        System.out.println("Extracting size " + N_GRAM_SIZE + " ngrams from " + inputPosts.size() + " Documents...");
        // each doc key maps to a list of its ngrams
        List<List<String>> documentNgrams = extractNGrams(inputPosts, token);

        // this is a little gross
        // how many times each ngram occurs in total in the corpus	// how many documents each ngram occurs in
        Pair<Map<String, Double>, Map<String, Double>> frequencies = getTotalFrequencyCounts(documentNgrams);
        Map<String, Double> totalFrequencies = frequencies.getValue0();
        Map<String, Double> documentOccurances = frequencies.getValue1();

        System.out.println("Keeping top ngrams...");
        PriorityQueue<Pair<Double, String>> chosenNgrams = topNGrams(totalFrequencies, documentOccurances);

        System.out.print("Creating vectors");
        Map<String, Integer> nGramIndices = nGramsToIndices(chosenNgrams);
        return createVectors(nGramIndices, documentNgrams, documentOccurances, inputPosts.size());

    }

    public static List<List<String>> extractNGrams(List<String> inputTexts, TokenType token)
    {
        List<List<String>> documentNgrams = new ArrayList<List<String>>();
        for (String text : inputTexts) {
            if (ALL_LOWER)
                text = text.toLowerCase();

            String[] words = text.split("\\s+");
            List<String> ngrams = extractDocumentTerms(words, token);
            documentNgrams.add(ngrams);
        }
        return documentNgrams;
    }

    private static List<String> extractDocumentTerms(String[] words, TokenType token)
    {
        List<String> ngramsFound = new ArrayList<String>();

        for (String word : words)
        {
            // we are only caring about tf-idf
            if (token == TokenType.TERMS)
                ngramsFound.add(word);
            else if(token == TokenType.STEMS)
            {
                String s = PorterStemmer.apply(word);
                ngramsFound.add(s);
            }
            // if ngram is small enough just add it
            else if (word.length() <= N_GRAM_SIZE)
            {
                ngramsFound.add(word);
            }
            // else do sliding window over each NGRAMSIZE block of the word
            else
            {
                for (int i = 0; i <= word.length()-N_GRAM_SIZE; i++)
                {
                    ngramsFound.add(word.substring(i, i+N_GRAM_SIZE));
                }
            }
        }
        return ngramsFound;
    }

    /**
     *
     * @param docNgrams map of each documents key to a list of its ngrams
     * @return [0] the total frequency count of each ngram, [1] the number of documents each ngram occurs in
     */
    private static Pair<Map<String, Double>, Map<String, Double>> getTotalFrequencyCounts(List<List<String>> docNgrams)
    {
        // how many times each ngram occurs in total in the corpus
        Map<String, Double> totalFrequencies = new HashMap<String, Double>();
        // how many documents each ngram occurs in
        Map<String, Double> documentOccurances = new HashMap<String, Double>();

        for (List<String> ngrams : docNgrams)
        {
            Set<String> resultSet = new HashSet<String>();
            for (String ngram : ngrams)
            {
                // how many times each ngram occurs overall in dataset
                if (totalFrequencies.containsKey(ngram))
                    totalFrequencies.put(ngram, totalFrequencies.get(ngram) + 1);
                else
                    totalFrequencies.put(ngram, 1.);
                // how many documents ngram occurs in -only add once for this document
                if (!resultSet.contains(ngram))
                {
                    if (documentOccurances.containsKey(ngram))
                        documentOccurances.put(ngram, documentOccurances.get(ngram) + 1);
                    else
                        documentOccurances.put(ngram, 1.);
                    resultSet.add(ngram);
                }
            }
        }
        return new Pair<Map<String, Double>, Map<String, Double>>(totalFrequencies, documentOccurances);
    }

    /**
     * select and keep only the TOP_NGRAM_K ngrams
     * @return
     */
    private static PriorityQueue<Pair<Double, String>> topNGrams(Map<String, Double> totalFrequencies, Map<String, Double> documentOccurances)
    {
        // use priority queue for heap sort
        PriorityQueue<Pair<Double, String>> topNGrams = new PriorityQueue<Pair<Double, String>>(TOP_NGRAM_K);
        String ngram;
        double occurances;

        int size = documentOccurances.size();
        // look at how many times each ngram occured
        for (Entry<String, Double> e : totalFrequencies.entrySet())
        {
            ngram = e.getKey();
            occurances = e.getValue();
            // if it did not occur in atleast MIN DOC documents, throw it out
            if (documentOccurances.get(ngram) >= MIN_DOC_OCCURANCES)
            {
                // if heap is not full, toss the ngram in
                if (topNGrams.size() < TOP_NGRAM_K)
                {
                    topNGrams.add(new Pair<Double, String>(occurances, ngram));
                }
                // if this ngram occurred enough to be in heap, put it in, remove lowest value ngram
                else if(occurances > topNGrams.peek().getValue0())
                {
                    topNGrams.poll().getValue1();
                    topNGrams.add(new Pair<Double, String>(occurances, ngram));
                }
            }
        }
        System.out.println("Keping at most top " + TOP_NGRAM_K + " ngrams out of " + size);
        return topNGrams;
    }

    /**
     * map the ngrams we're keeping to indices
     * @return the ngram-index map
     */
    private static Map<String, Integer> nGramsToIndices(PriorityQueue<Pair<Double, String>> nGrams)
    {
        // map full ngram set to common indices
        Map<String, Integer> nGramIndices = new HashMap<String, Integer>();
        int index = 0;
        for ( Pair<Double, String> ngram : nGrams)
            nGramIndices.put(ngram.getValue1(), index++);
        return nGramIndices;
    }

    public static List<SparseTensor1> createVectors(Map<String, Integer> nGramIndices, List<List<String>> documentNGrams,
                                                      Map<String, Double> documentOccurances, double size)
    {
        System.out.print(" size " + nGramIndices.size() + "...");

        List<SparseTensor1> tensors = new ArrayList<SparseTensor1>();
//        if (THREAD_SAFE){
//            tensors = new HashMap<Integer, SparseTensor1>();
//        }else{
//            tensors = new ConcurrentHashMap<Integer, SparseTensor1>();
//        }

        for (List<String> document : documentNGrams)
        {
            Map<String, Double> postCounts = new HashMap<String, Double>();

            // figure out the term frequency counts of each ngram that occurred in this post
            for (String ngram : document)
            {
                if (postCounts.containsKey(ngram))
                    postCounts.put(ngram, postCounts.get(ngram) + 1);
                else
                    postCounts.put(ngram, 1.);
            }

            SparseTensor1 tensor = getTFIDFVector(nGramIndices, postCounts, documentOccurances, size, document.size());
            tensors.add(tensor);
        }
        System.out.println("Done");
        return tensors;
    }

    private static SparseTensor1 getTFIDFVector(Map<String, Integer> nGramIndices,Map<String, Double> postCounts,
                                           Map<String, Double> documentOccurances, double collectionSize, double docSize)
    {
        SparseTensor1 tensor = new SparseTensor1(nGramIndices.size());
        double tf, idf;

        // for each ngram that occurred in the post, get its tfidf
        for (Entry<String, Double> ngramFreq : postCounts.entrySet())
        {
            String ngram = ngramFreq.getKey();
            // only use ngrams that were not culled by minimum occurrence requirements
            if (nGramIndices.containsKey(ngram))
            {
                tf = ngramFreq.getValue();
                if (IDF)
                    // multiply by inverse document frequency
                    idf = Math.log(collectionSize / (Double.MIN_VALUE+documentOccurances.get(ngram)));
                else
                    idf=1;
                tensor.update(nGramIndices.get(ngram), (tf*idf));
            }
        }
        tensor.twoNormalize();
        return tensor;
    }

    public enum TokenType{TERMS, NGRAMS, STEMS};

    public static void main(String[] args)
    {
        List<String> posts = new ArrayList<String>();
        String t1 = "test testing this";
        String t2 = "this is only a test";
        String t3 = "cat dog catdog";

        posts.add(t1);
        posts.add(t2);
        posts.add(t3);

        List<SparseTensor1> tensors = TFIDFVectors.run(posts);
        System.out.println(tensors.get(0).cosineSimilarity(tensors.get(2)));
        System.out.println(tensors.get(0).cosineSimilarity(tensors.get(3)));

    }
}
