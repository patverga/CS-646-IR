package co.pemma

import java.io.{BufferedWriter, File, FileWriter}

import cc.factorie.app.strings.PorterStemmer
import cc.factorie.app.topics.lda.{Document, LDA}
import cc.factorie.directed.DirectedModel
import cc.factorie.la.{Tensor1, DenseTensor1, SparseTensor1}
import cc.factorie.variable.CategoricalSeqDomain
import edu.umass.ciir.strepsimur.galago._
import edu.umass.ciir.strepsimur.galago.stopstructure.StopStructuring
import org.lemurproject.galago.core.retrieval.query.{Node, StructuredQuery}
import org.lemurproject.galago.core.retrieval.{Retrieval, ScoredDocument}
import org.lemurproject.galago.utility.Parameters

import scala.collection.JavaConverters._
import scala.collection.mutable
import scala.io.Source
import scala.util.Random

/**
 * Created by pv on 11/17/14.
 */
object ClusterRelevanceFeedback extends App {
  val numClusterDocs = 100
  val numExpansionClusters = 5
  val minSim = .25
  val numDocs = 1000
  val numTerms = 50
  val numExpansionDocs = 10
  val lambdaProb = 1269.0
  val lambdaQueryExpand = .55
  val clusterK = 5

  val params = ExpansionModels.getCollectionParams("robust")
  val collection = "robust-community "

  queryExpand(collection)

  def queryExpand(collection : String) =
  {
    // make sure output dir exists and clear old results
    val outputLocation = s"output/$collection"
    new File("output").mkdir()
    Seq("cluster", "rm", "ql", "lda", "qlda", "combined").foreach(fileName=> new File(s"output/$collection-$fileName").delete())

    val indexLocation = if (collection == "books") "../index/book-index" else "../index/robust-index"
    val searcher: GalagoSearcher = {
      val indexParam = new Parameters()
      indexParam.set("index", indexLocation)
      GalagoSearcher(indexParam)
    }
    val defaultStopStructures = new StopStructuring(searcher.getUnderlyingRetrieval())

    val querySource = Source.fromFile(s"./queries/$collection")
    val queries = querySource.getLines().toList.map(q => {
      val parts = q.split("\t")
      (parts(0), parts(1))
    })//.filter{case(qid,_) => Integer.parseInt(qid) >= 600} // only use last queries

    queries.foreach { case (qid, query) =>
      println(s"Running query number $qid : $query.")
      val cleanQuery = defaultStopStructures.removeStopStructure(query)
      // convert query to galago form
      val galagoQuery = GalagoQueryBuilder.seqdep(cleanQuery).queryStr
      // get initial results
      val rankings = searcher.retrieveScoredDocuments(galagoQuery, Some(params), numDocs)
      // export initial rankings for comparison
      exportResults(qid, s"$outputLocation-ql", rankings)
      // get text of top docs
      val docStrings = rankings.take(numClusterDocs).map(d => parseRobust(searcher.pullDocument(d.documentName, params).text))//.replaceAll("[^a-zA-Z 0-9]", "").toLowerCase)

      // cluster expansion using tfidf
      val tfidfTensors = TFIDFVectors.run(docStrings.toList.asJava).asScala
      val clusterDocs = chooseClusterDocs(rankings take numClusterDocs, tfidfTensors, docStrings, cleanQuery, searcher).sortBy(-_.score)
      queryExpansion(clusterDocs, searcher, qid, galagoQuery, s"$outputLocation-cluster")

      // cluster expansion using LDA topic distribution vectors
      val (lda, ldaTensors) = LDAVectors(docStrings, 100)
      val ldaDocs = chooseClusterDocs(rankings take numClusterDocs, ldaTensors, docStrings, cleanQuery, searcher).sortBy(-_.score)
      queryExpansion(ldaDocs, searcher, qid, galagoQuery, s"$outputLocation-lda")

      // query based LDA cluster
      val queryLdaDoc = new Document(lda.wordSeqDomain, "query", cleanQuery.split("\\s+").toSeq)
      lda.inferDocumentTheta(queryLdaDoc)
      val queryLdaTensor = new DenseTensor1(queryLdaDoc.thetaArray)
      val queryLdaDocs = kNN(queryLdaTensor, ldaTensors, 0, numExpansionDocs).map(rankings(_))
      queryExpansion(queryLdaDocs, searcher, qid, galagoQuery, s"$outputLocation-qlda")

      // combine tfidf and lda vectors
      val combinedTensors = tfidfTensors.zipWithIndex.map{case (tensor, i) =>
        val ldaTensor = ldaTensors(i)
        val combined = new SparseTensor1( tensor.size + ldaTensor.size)
        tensor.foreachActiveElement{ case (dex, value) =>
            combined.update(dex, value)
        }
        ldaTensor.foreachElement{ case (dex, value) => combined.update(tensor.size+dex, value) }
        combined.twoNormalize()
        combined
      }
      val combinedDocs = chooseClusterDocs(rankings take numClusterDocs, combinedTensors, docStrings, cleanQuery, searcher).sortBy(-_.score)
      queryExpansion(combinedDocs, searcher, qid, galagoQuery, s"$outputLocation-combined")

      // relevance model expansion terms using all top docs
      var rmDocs = rankings
//      for (i<- 1 to 15) {
        rmDocs = queryExpansion(rmDocs, searcher, qid, galagoQuery, s"$outputLocation-rm")
//      }
    }
  }

  def queryExpansion(docs: Seq[ScoredDocument], searcher : GalagoSearcher, qid : String, galagoQuery : String, outLocation : String)
  : Seq[ScoredDocument] ={
    val expansionTerms = ExpansionModels.lce(docs take numExpansionDocs, searcher, numTerms, "robust")
    val expansionRankings = ExpansionModels.runExpansionQuery(galagoQuery, expansionTerms, "robust", searcher)
    exportResults(qid, outLocation, expansionRankings)
    expansionRankings
  }

  def chooseClusterDocs(rankings :Seq[ScoredDocument], tensors : Seq[Tensor1], docStrings: Seq[String], query : String,
                        searcher: GalagoSearcher): Seq[ScoredDocument] =
  {
    // find knn for each doc
    val clusters = tensors.zipWithIndex.map { case (t1, i) =>
      kNN(t1, tensors, i, clusterK)
    }
    val stemmedQuery = query.split("\\s+")//.map(PorterStemmer.apply)
    // score each cluster, sort by the score, take top k (numexpansionclusters), and map to their indices
    val bestClusters = clusters.map(scoreCluster(_, docStrings, stemmedQuery, searcher)).zipWithIndex.sortBy(-_._1).take(numExpansionClusters).map(_._2)
    // return the scored documents from the best k clusters
    bestClusters.flatMap(clusters(_).map(rankings(_)))
  }

  def kNN(t1 : Tensor1, tensors : Seq[Tensor1], i : Int, k :Int): Seq[Int] = {
    val heap = new mutable.PriorityQueue[(Double, Int)]()
    for (j <- i + 1 to tensors.size - 1) {
      val t2 = tensors(j)
      val sim = t1.cosineSimilarity(t2)
      if (sim > minSim) {
        if (heap.size < k) heap.enqueue(sim -> j)
        else if (sim > heap.head._1) {
          // if the score is greater the min, then add to the heap
          heap.dequeue()
          heap.enqueue(sim -> j)
        }
      }
    }
    heap.enqueue(1.-> i)
    heap.map(_._2).toSeq
  }

  def runExpandedQuery (expandedQuery : String, qid : String, out : String, searcher : GalagoSearcher)
  : Seq[ScoredDocument] = {
    println("running query: " + expandedQuery)
    val scoredDocs = searcher.retrieveScoredDocuments(expandedQuery, Some(params), 100)
    exportResults(qid, out, scoredDocs)
    scoredDocs
  }

  def exportResults(qid: String, out: String, scoredDocs: Seq[ScoredDocument]) {
    val p = new java.io.PrintWriter(new BufferedWriter(new FileWriter(s"$out", true)))
    try {
      scoredDocs.foreach(doc => p.write(doc.toTRECformat(qid) + "\n"))
    }
    finally {
      p.close()
    }
  }

  def scoreCluster(cluster: Iterable[Int], docStrings: Seq[String], query : Iterable[String], searcher : GalagoSearcher)
  : Double = {
    // get freq of each term in the cluster
    val clWords = cluster.flatMap(index => docStrings(index).split("\\s+"))//.map(PorterStemmer.apply)
    val clWordCounts = clWords.foldLeft(Map.empty[String, Double]) {
      (count, word) => count + (word -> (count.getOrElse(word, 0.0) + 1.0))
    }
    // P(query | cluster)
    query.map( w => {
      // P(w | cluster)
      val pMlClust = clWordCounts.getOrElse(w, 0.0) / clWords.size
      val pmlClustWeight = clWords.size / (clWords.size + lambdaProb)
      // P(w | collection) : term freq in collection  / collection length
      val pMlColl = collectionTermFreq(w, searcher.getUnderlyingRetrieval()) / collectionLength(searcher.getUnderlyingRetrieval())
      val pMlCollWeight = lambdaProb / (clWords.size + lambdaProb)
      Math.log( (pmlClustWeight * pMlClust) + (pMlCollWeight * pMlColl) )
    }).sum
  }

  def collectionTermFreq(query: String, r: Retrieval): Double = {
    var node = StructuredQuery.parse(query)
    node.getNodeParameters.set("queryType", "count")
    node = r.transformQuery(node, new Parameters())
    r.getNodeStatistics(node).nodeFrequency
  }

  def collectionLength(r: Retrieval): Double = {
    val n = new Node()
    n.setOperator("lengths")
    n.getNodeParameters.set("part", "lengths")
    r.getCollectionStatistics(n).collectionLength
  }

  def LDAVectors(docStrings : Iterable[String], K : Int): (LDA, Seq[DenseTensor1]) =
  {
    val domain = new CategoricalSeqDomain[String]
    val lda = new LDA(domain,K,50.0/K,.01,100)(DirectedModel(), Random)
    docStrings.toSet[String].foreach(s => lda.addDocument(Document.fromString(domain,s,s),new Random()))
    lda.inferTopics()
    (lda, docStrings.map(doc => {
      val tensor = new DenseTensor1(lda.getDocument(doc).thetaArray)
//      tensor.twoNormalize
      tensor
    }).toSeq)
  }


  def parseRobust(robustXml : String) : String =
  {
    val headline = if (robustXml.contains("<HEADLINE>")){
      robustXml.split("<HEADLINE>",2)(1).split("</HEADLINE>",2)(0)
    } else ""
    val text = if (robustXml.contains("<TEXT>")){
      robustXml.split("<TEXT>",2)(1).split("</TEXT>",2)(0)
    } else ""
    // combine headline and body
    val combined = if (text != "") headline + " " + text
    else robustXml
    // strip out remaining tags such as <P>
    combined.replaceAll("<.*>","").replaceAll("\\p{P}", "").trim
  }
}