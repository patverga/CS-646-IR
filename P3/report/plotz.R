library(plyr)
library(ggplot2)
library(foreach)
library(grid)
library(stringr)
library(scales)

path="/home/pv/CS-646-IR/P3"
data <-  read.table(paste(path, "results", sep="/"), header=F, stringsAsFactors=F)
colnames(data)<- c('data','map', 'ndcg20', 'p10')
data$data <- sapply(strsplit(data$data, "/"), "[[",2)

split_type <- function(s){
  index <- str_count(s, '-')
  split <- strsplit(s, "-")[[1]]
  data.set <- paste(split[1:index], collapse='-')
  type <- split[index+1]
  return(cbind(data.set=data.set, type=type))
}

data.2 <-data.frame(data, t(data.frame(sapply(data$data, split_type))), stringsAsFactors=F)
colnames(data.2)<- c('data','map', 'ndcg20', 'p10', 'data.set', 'type')

data.3 <- data.frame(rbind(cbind(data=data.2$data, val=as.numeric(data.2$map), data.set=data.2$data.set, type=data.2$type, metric='map'),
                cbind(data=data.2$data, val=as.numeric(data.2$p10), data.set=data.2$data.set, type=data.2$type, metric='p10'),
                cbind(data=data.2$data, val=as.numeric(data.2$ndcg20), data.set=data.2$data.set, type=data.2$type, metric='ndcg20')),
                stringsAsFactors=F)

ordering <- c("ql","lda", "qlda", "cluster", "rm", "combined")
data.3$val = as.numeric(data.3$val)

plots <- ggplot(data.3, aes(x=type, y=val, fill=type)) + 
  geom_bar(colour="black", stat="identity") +
  scale_y_continuous(breaks=seq(0,.6,.05)) + 
  facet_grid(data.set~metric, scales="free") + 
  labs( x='Algorithm', y='Value', color='Algorithm', fill='Algorithm') + 
  theme(legend.position="top", panel.margin = unit(.4, "cm")) + 
#  guides(col = guide_legend(nrow = 2)) + 
  scale_x_discrete(limits=ordering) + 
  scale_fill_discrete(limits=ordering) +
  coord_cartesian(ylim=c(.2,.6))
print(plots)

####

ggsave(paste(path, 'report', 'results.pdf',sep='/'), plots, width = 8, height = 8)
