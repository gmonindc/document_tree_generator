
import string
import random
import os
import re
import cPickle

number_of_words=150

def wordcount(txt):
	
	cntdict={}
	for w in re.findall(r"""([a-z]{3,40})""",txt.lower()):
		cntdict[w]=1
	for w in re.findall(r"""([a-z]{3,40} [a-z]{3,40})""",txt.lower()):
		cntdict[w]=1
	return cntdict


#find two documents which have very few common keywords
#use these two most dissimilar documents to create two word list
def find_dissimilar_documents(file_list):
	lowscore=1000.0
	for fn1 in file_list[:len(file_list)/2]:
		for fn2 in file_list[len(file_list)/2:]:
			f=open(fn1)
			txt=f.read()[:10000]
			f.close()
			rwcnt=wordcount(txt)
			f=open(fn2)
			txt=f.read()[:10000]
			f.close()
			lwcnt=wordcount(txt)
			collision=0
			for w in rwcnt:
				if lwcnt.has_key(w):
					collision+=1
			collision=100.0*collision/(len(rwcnt)+len(lwcnt))
			if collision<lowscore:
				print fn1,fn2,collision
				lowscore=float(collision)
				right_kw=dict(rwcnt)
				left_kw=dict(lwcnt)
	return right_kw,left_kw

#check a new set of documents and check to see if they are more like the first or second word list
#separate out this new document set into two separate document lists
def split_document_list_with_keywords(file_list,bestrw,bestlw):
	scoredict={}
	for fn in file_list:
		f=open(fn)
		txt=f.read()
		f.close()
		score=random.random()/100.0
		for kw in bestrw:
			if string.find(txt.lower(),kw)>-1:
				score+=1
		for kw in bestlw:
			if string.find(txt.lower(),kw)>-1:
				score-=1
		scoredict[fn]=score

	score_list=scoredict.values()
	score_list.sort()

	rightlist=[]
	leftlist=[]
	for fn in file_list:
		if scoredict[fn]>=score_list[len(score_list)/2]:
			rightlist.append(fn)
		else:
			leftlist.append(fn)
	return rightlist,leftlist
	
#use the right and left documents lists to create two new keyword lists
def generate_split_keywords_from_document_lists(rightlist,leftlist):	
	word_score={}
	net_count={}
	
	#words on the right are scored +1
	for fn in rightlist:
		f=open(fn)
		txt=f.read()
		f.close()
		wcnt=wordcount(txt)
		for w in wcnt:
			if word_score.has_key(w):
				word_score[w]+=1
				net_count[w]+=1
			else:
				word_score[w]=1+random.random()/100.0
				net_count[w]=1

	#words on the left are scored -1
	for fn in leftlist:
		f=open(fn)
		txt=f.read()
		f.close()
		wcnt=wordcount(txt)
		for w in wcnt:
			if word_score.has_key(w):
				word_score[w]-=1
				net_count[w]+=1
			else:
				word_score[w]=-1+random.random()/100.0
				net_count[w]=1

	net_count_scores=net_count.values()
	net_count_scores.sort()

	#words must be used more than the mode
	for w in net_count:
		if net_count[w]<net_count_scores[len(net_count_scores)/2]:
			del word_score[w]

	score_list=word_score.values()
	score_list.sort()

	#generate the final left and right word set
	rightwords={}
	leftwords={}
	for w in word_score:
		if word_score[w]<=score_list[number_of_words]:
			leftwords[w]=1
		elif word_score[w]>=score_list[-number_of_words]:
			rightwords[w]=1

	return rightwords,leftwords


def split_document_list(file_list):
	interations=3
	tmp_filelist=list(file_list)
	random.shuffle(tmp_filelist)
	right_kw,left_kw=find_dissimilar_documents(tmp_filelist[:100])
	for i in range(interations):
		tmp_filelist=list(file_list)
		random.shuffle(tmp_filelist)
		right_doc_list,left_doc_list=split_document_list_with_keywords(tmp_filelist[:100],right_kw,left_kw)
		right_kw,left_kw=generate_split_keywords_from_document_lists(right_doc_list,left_doc_list)
		print right_kw
		print left_kw
	right_doc_list,left_doc_list=split_document_list_with_keywords(file_list,right_kw,left_kw)
	print len(right_doc_list)
	print len(left_doc_list)
	return right_doc_list,left_doc_list,right_kw,left_kw

def add_doc(document_tree,fn):
	spot='top'
	doc_list,right_kw,left_kw=document_tree[spot]
	f=open(fn)
	txt=f.read()
	f.close()
	done=False
	while not done:
		right_score,left_score=0,0
		for kw in right_kw:
			if string.find(txt.lower(),kw)>-1:
				right_score+=1
		for kw in left_kw:
			if string.find(txt.lower(),kw)>-1:
				left_score+=1
		if right_score>left_score:
			spot+='r'
		else:
			spot+='l'
		doc_list,right_kw,left_kw=document_tree[spot]
		if len(right_kw)==0:
			doc_list.append(fn)
			document_tree[spot]=doc_list,right_kw,left_kw
			done=True
	return document_tree

def rebalance_tree(document_tree):
	done=False
	while not done:
		done=True
		dtl=document_tree.keys()
		for dtk in dtl:
			doc_list,right_kw,left_kw=document_tree[dtk]
			if len(doc_list)>2000:
				print 'splitting',dtk,len(doc_list)
				right_doc_list,left_doc_list,right_kw,left_kw=split_document_list(doc_list)
				document_tree[dtk]=([],right_kw,left_kw)
				document_tree[dtk+'r']=(right_doc_list,[],[])
				document_tree[dtk+'l']=(left_doc_list,[],[])
				done=False
	return document_tree


def search_tree(document_tree,txt):
	spot='top'
	doc_list,right_kw,left_kw=document_tree[spot]
	done=False
	while not done:
		right_score,left_score=0,0
		for kw in right_kw:
			if string.find(txt.lower(),kw)>-1:
				right_score+=1
		for kw in left_kw:
			if string.find(txt.lower(),kw)>-1:
				left_score+=1
		if right_score>left_score:
			spot+='r'
		else:
			spot+='l'
		doc_list,right_kw,left_kw=document_tree[spot]
		if len(right_kw)==0:
			done=True
	return doc_list


file_list=[]
dlist=os.listdir('/home/gmoney/uspto/pats')
random.shuffle(dlist)
for directory in dlist[:4]:
	print '/home/gmoney/uspto/pats/'+directory
	for path,dirs,files in os.walk('/home/gmoney/uspto/pats/'+directory):
		for f in files:
			fn=path+'/'+f
			file_list.append(fn)

dlist=os.listdir('/home/gmoney/uspto/pgpub')
random.shuffle(dlist)
dlist2=os.listdir('/home/gmoney/uspto/pgpub/'+dlist[0])
random.shuffle(dlist2)
for directory in dlist2[:4]:
	print '/home/gmoney/uspto/pgpub/'+dlist[0]+'/'+directory
	for path,dirs,files in os.walk('/home/gmoney/uspto/pgpub/'+dlist[0]+'/'+directory):
		for f in files:
			fn=path+'/'+f
			file_list.append(fn)

print 'documents to sort',len(file_list)

try:
	f=open('test_tree.bin')
	document_tree=cPickle.load(f)
	f.close()	
except:	
	document_tree={}
	right_doc_list,left_doc_list,right_kw,left_kw=split_document_list(file_list)
	document_tree['top']=([],right_kw,left_kw)
	document_tree['topr']=(right_doc_list,[],[])
	document_tree['topl']=(left_doc_list,[],[])

#~ f=open('/home/gmoney/uspto/pgpub/2006/009/20060097625.txt')
#~ txt=f.read()
#~ f.close()
#~ for fn in search_tree(document_tree,txt):
	#~ print fn
#~ asdf

used_dict={}
dtl=document_tree.keys()
for dtk in dtl:
	doc_list,right_kw,left_kw=document_tree[dtk]
	for doc in doc_list:
		used_dict[doc]=1

print 'number of patents in tree',len(used_dict)

cnt=0
for fn in file_list:
	cnt+=1
	if not used_dict.has_key(fn):
		used_dict[fn]=1
		document_tree=add_doc(document_tree,fn)
	else:
		print 'used',fn
	if cnt % 100 == 0:
		print 100.0*cnt/len(file_list),'% done'

document_tree=rebalance_tree(document_tree)

f=open('test_tree.bin','wb')
cPickle.dump(document_tree,f)
f.close()

