test:
	make clean
	make encode
	make decode
	md5sum short.tar short.tar.decoded

encode:
	python3 encode.py short.tar
	-ls -l chunks.data short.tar.encoded

decode:
	python3 decode.py short.tar

clean:
	-rm chunks.data
	-rm short.tar.encoded short.tar.decoded
	-rm -r -f __pycache__/
